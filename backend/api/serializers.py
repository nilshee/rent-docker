from django.contrib.auth.models import User, Group, Permission
from rest_framework import serializers
from rest_framework.exceptions import ParseError
from rest_framework.request import Request
from rest_framework import validators
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from django.forms import model_to_dict
import logging
import re
from base.models import Category, RentalObject, RentalObjectType, Reservation, Rental, Tag, Text, Profile
from base import models
from datetime import timedelta, datetime

logger = logging.getLogger(name="django")


class RentalObjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalObjectType
        fields = '__all__'


class MaxRentDurationSerializer(serializers.ModelSerializer):
    duration_in_days = serializers.SerializerMethodField(
        'get_duration_in_days', required=False)

    class Meta:
        model = models.MaxRentDuration
        fields = '__all__'

    def get_duration_in_days(self, obj):
        """
        since parsing of the timedelta is tidious we add another field with the timedelta in days
        """
        if type(obj) is not dict:
            obj = model_to_dict(obj)
        return int(obj['duration'].days)

    def create(self, validated_data):
        validated_data['duration'] = timedelta(
            days=validated_data['duration'].total_seconds())
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['duration'] = timedelta(
            days=validated_data['duration'].total_seconds())
        return super().update(instance, validated_data)


class PrioritySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Priority
        fields = '__all__'


class ProfileSerializer(serializers.ModelSerializer):
    prio = PrioritySerializer(required=False)
    class Meta:
        model = Profile
        fields = '__all__'


class UserCreationSerializer(serializers.HyperlinkedModelSerializer):
    """
    Used for user registration 
    """
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['url', 'username', 'password', 'email',
                  'groups', 'id', 'first_name', 'last_name', 'profile']

    def validate_email(self, email):
        """
        overwrite the email validation to prevent multiuse of emails. Validate Email corresponding to a specific regex
        """
        regex = re.compile(models.Settings.objects.get(
            type='email_validation_regex').value)
        result = regex.fullmatch(email)
        if not (result and result.group(0) == email):
            raise serializers.ValidationError("Email ist im falsche Format")
        if User.objects.all().filter(email=email).count() > 0:
            raise serializers.ValidationError("Email bereits in Benutzung")
        return email

    @transaction.atomic
    def create(self, validated_data):
        """
        creates the user object in db and disables the login. also creates a profile with the supllied data. profile MUST be set. 
        """
        validated_data['is_active'] = False
        if 'groups' in validated_data:
            del validated_data['groups']
        profile_data = validated_data.pop('profile')
        user = User.objects.create_user(**validated_data)
        profile_data['user'] = user.pk
        profile_serializer = ProfileSerializer(data=profile_data)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()
        return user


class UserSerializer(serializers.HyperlinkedModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        #fields = '__all__'
        fields = ['url', 'username', 'email',
                  'groups', 'id', 'first_name', 'last_name', 'profile']

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        user = User.objects.create(**validated_data)
        Profile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance: User, validated_data: dict):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        # Profile is not neccessarily needed to update User
        try:
            profile_data = validated_data.pop('profile')
            profile = instance.profile
        except Profile.DoesNotExist:
            return instance
        except KeyError:
            return instance

        ProfileSerializer.update(profile, profile, profile_data)

        return instance


class AdminUserSerializer(serializers.ModelSerializer):
    profiledata = ProfileSerializer(required=False, read_only=True, source='profile')
    has_lending_rights = serializers.SerializerMethodField(required=False, read_only=True)
    class Meta:
        model = User
        exclude = ['password']
        include = ['profiledata']

    def get_has_lending_rights(self,obj:User)->bool:
        ret = False
        
        for permission in obj.get_user_permissions():
            if 'lending_access' in permission:
                logger.info(permission)
                ret = True
        return ret



class KnowLoginUserSerializer(serializers.ModelSerializer):
    user_permissions = serializers.SerializerMethodField(
        'get_user_permissions_name')

    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'groups',
                  'is_staff', 'is_superuser', 'user_permissions', 'profile', 'id']

    def get_user_permissions_name(self, obj):
        # replace ids with Permission names to reduce the number of requests
        return obj.get_all_permissions()


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class RentalObjectSerializer(serializers.ModelSerializer):
    currently_in_house = serializers.SerializerMethodField(
        required=False, read_only=True)
    merged_identifier = serializers.SerializerMethodField(
        required=False, read_only=True)

    class Meta:
        model = RentalObject
        fields = '__all__'

    def get_currently_in_house(self, obj: models.RentalObject) -> bool:
        return obj.rental_set.filter(Q(Q(handed_out_at__lte=timezone.now()) & Q(Q(received_back_at__gte=timezone.now()) | Q(received_back_at__isnull=True)))).count() == 0

    def get_merged_identifier(self, obj: models.RentalObject) -> str:
        return obj.type.prefix_identifier + str(obj.internal_identifier)


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'description', 'id')


class BulkReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Reservation
        fields = '__all__'
        validators = [
            validators.UniqueTogetherValidator(
                queryset=models.Reservation.objects.all(),
                fields=['reserver', 'operation_number', 'objecttype'],
                message="This Combination of reserver, operation_number and object_type already exists"
            ),
        ]

    def validate(self, data):
        objectType = models.RentalObjectType.max_rent_duration(pk=data['objecttype'].pk, prio=data['reserver'].prio)
        if type(objectType) is not dict and model_to_dict(objectType)['duration'] + timedelta(days=7) < data['reserved_until']-data['reserved_from']:
            raise serializers.ValidationError(
                detail="the rent duration exceeds max_rent_duration.")
        if data['reserved_from'].isoweekday() != int(models.Settings.objects.get(type='lenting_day').value):
            raise serializers.ValidationError(
                detail="this day is not a lenting day therefore a reservation can not start here")
        if data['reserved_until'].isoweekday() != int(models.Settings.objects.get(type='returning_day').value):
            raise serializers.ValidationError(
                detail="this day is not a returning day therefore a reservation can not end here")
        if data['reserved_from'] >= data['reserved_until']:
            raise serializers.ValidationError(
                detail="reserved_from must be before reserved_until")
        if data['count'] > models.RentalObjectType.available(pk=data['objecttype'], from_date=data['reserved_from'], until_date=data['reserved_until'])['available']:
            raise serializers.ValidationError(
                detail="There are not enough objects of this type to fullfill your reservation")
        return data


class ReservationProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = models.Profile
        fields = '__all__'


class ReservationSerializer(serializers.ModelSerializer):
    objecttype = RentalObjectTypeSerializer(read_only=True)
    fullfilled = serializers.SerializerMethodField(
        required=False, read_only=True) 

    class Meta:
        model = models.Reservation
        #fields = '__all__'
        exclude = ['reserver', 'notified']

    def get_fullfilled(self, obj):
        return obj.rental_set.filter(handed_out_at__isnull=False).count() > 0


class ReservationAdminSerializer(serializers.ModelSerializer):
    reserver = ReservationProfileSerializer(read_only=True)
    objecttype = RentalObjectTypeSerializer(read_only=True)
    fullfilled = serializers.SerializerMethodField(
        required=False, read_only=True)

    class Meta:
        model = models.Reservation
        fields = '__all__'

    def get_fullfilled(self, obj):
        return obj.rental_set.all().count() > 0


class RentalSerializer(serializers.ModelSerializer):
    rented_object = RentalObjectSerializer(required=False, read_only=True)
    reservation = ReservationAdminSerializer(required=False, read_only=True)
    extendable = serializers.SerializerMethodField(
        required=False, read_only=True)
    extended_until = serializers.SerializerMethodField(
        required=False, read_only=True)
    extended_count = serializers.SerializerMethodField(
        required=False, read_only=True)

    class Meta:
        model = Rental
        fields = '__all__'

    def validate_reserved_until(self, reserved_until):
        """
        enforce that we do not overlap rentals on one object
        """
        if self.instance.reserved_until != reserved_until and models.RentalObjectType.available(pk=self.instance.rented_object.type.pk, from_date=self.instance.reserved_until +
                                                                                                settings.DEFAULT_OFFSET_BETWEEN_RENTALS, until_date=reserved_until)['available'] == 0:
            raise serializers.ValidationError(
                "reserved until overlaps with a reservation or rental")
        return reserved_until
    
    def get_extended_until(self, obj:Rental) -> datetime:
        """
        add a field to check until when an item is rented
        """
        return obj.extended_until()
    
    def get_extended_count(self, obj:Rental) -> int:
        return obj.extension_set.count()

    # default extension time = 1 week
    def get_extendable(self, obj) -> bool:
        """
        checking if the object is extendable by 1 week returns true if it is
        """
        # reserved_from + offset should result in the reseved + offset + offset for reparations
        available = models.RentalObjectType.available(pk=obj.rented_object.type.pk, from_date=self.get_extended_until(obj) +
                                                      settings.DEFAULT_OFFSET_BETWEEN_RENTALS, until_date=self.get_extended_until(obj)+timedelta(weeks=1))
        return available["available"] >= 1


class RentalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class TextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Text
        fields = '__all__'


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Settings
        fields = ['type', 'value', 'id']


class FilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Files
        fields = '__all__'


class SuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Suggestion
        fields = '__all__'
        validators = [
            validators.UniqueTogetherValidator(
                queryset=models.Suggestion.objects.all(),
                fields=['suggestion', 'suggestion_for'],
                message="you can not have the same combination of suggestion an suggestion twice"
            ),
        ]

class OnPremiseWorkplaceStatusSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    class Meta: 
        model = models.OnPremiseWorkplaceStatus
        #fields = '__all__'
        exclude = ['workplace']
        include = ['id']


class OnPremiseWorkplaceSerializer(serializers.ModelSerializer):
    status = OnPremiseWorkplaceStatusSerializer(many=True)
    image = serializers.ImageField(required=False)
    class Meta:
        model = models.OnPremiseWorkplace
        fields = '__all__'
        include = ['status']

    def create(self, validated_data):
        status = validated_data.pop('status')
        exclusions = validated_data.pop('exclusions')
        workplace = models.OnPremiseWorkplace.objects.create(**validated_data)
        for stat in status:
            models.OnPremiseWorkplaceStatus.objects.create(workplace_id=workplace.pk, **stat)
        for exclusion in exclusions:
            workplace.exclusions.add(exclusion)
        return workplace

    def update(self, instance:models.OnPremiseWorkplace, validated_data):
        if 'status' in validated_data:
            status = validated_data.pop('status')
            for stat in status:
                if 'id' in stat:
                    stat_mod = models.OnPremiseWorkplaceStatus.objects.filter(pk=stat['id'])
                    stat_mod.update(**stat)
                else:
                    stat_mod = models.OnPremiseWorkplaceStatus.objects.create(**stat, workplace_id=instance.pk)
                    instance.status.add(stat_mod)
                    instance.save()
        if 'exclusions' in validated_data:
            exclusions = validated_data.pop('exclusions')
            instance.exclusions.set(exclusions)
            instance.save()
        instance = super().update(instance=instance, validated_data=validated_data)
        # models.OnPremiseWorkplace.objects.filter(pk=instance.pk).update(**validated_data)
        # instance.refresh_from_db()
        return instance

class OnPremiseBookingSerializer(serializers.ModelSerializer):
    userobj = UserSerializer(read_only=True, required=False, source="user")
    class Meta:
        model = models.OnPremiseBooking
        fields = '__all__'
        include = ['userobj']

class OnPremiseBlockedTimesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OnPremiseBlockedTimes
        fields = '__all__'