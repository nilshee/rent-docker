from typing import Iterable, Optional
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, date
from django.forms import model_to_dict
import logging


logger = logging.getLogger(name="django")


class Priority(models.Model):
    prio = models.PositiveSmallIntegerField(
        verbose_name='priority in renting queue')
    name = models.CharField(
        max_length=100, verbose_name='name of the priority class')
    description = models.CharField(
        max_length=255, verbose_name='description of the priority class', null=True)

    def __str__(self) -> str:
        return self.name + ": " + str(self.prio)


class Profile(models.Model):
    """
    extension of User model for addtitional information. since we check those permissions through here we create them here. (Automatically created through the meta tag)
    """
    class Meta:
        permissions = [
            ("inventory_editing",
             "able to edit and create the inventory and got nearly full access"),
            ("lending_access", "is able to lend stuff")
        ]
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, blank=True, related_name="profile")
    # Since people are already somewhat authenticated through their email allow them to lend even without validation.On authorization validation a corresponding Prio field must be set
    prio = models.ForeignKey(
        Priority, on_delete=models.SET_NULL, null=True, blank=True, default=Priority.objects.get(prio=99).id)
    newsletter = models.BooleanField(
        verbose_name='newsletter signup', default=False, blank=True)
    automatically_verifiable = models.BooleanField(verbose_name="tells if someone is automatically verifiable, set to false if it fails", default=True, blank=True)
    # to remove the banner we will ask the user only for verification if the user is not verified yet
    verified = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.user.username


class Category(models.Model):
    """
    To categorize each RentalObjectType
    """
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self) -> str:
        return self.name


class RentalObjectType(models.Model):
    """
    Parenttype for objects
    """
    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='unique_id_prefix',
                fields=['prefix_identifier']
            )
        ]
    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='rentalobjecttypes')
    shortdescription = models.TextField(default='')
    description = models.TextField(default='')
    manufacturer = models.CharField(max_length=100, default='')
    # hide objects from rentalpage
    visible = models.BooleanField(default=False)
    image = models.ImageField(default='nopicture.png')
    prefix_identifier = models.CharField(max_length=20, default="LZ")
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self) -> str:
        return self.name

    def available(pk: int, from_date: datetime, until_date: datetime):
        if isinstance(from_date, date):
            from_date = datetime.combine(
                from_date, datetime.min.time(), tzinfo=timezone.get_current_timezone())
        if isinstance(until_date, date):
            until_date = datetime.combine(
                until_date, datetime.min.time(), tzinfo=timezone.get_current_timezone())
        delta = until_date - from_date
        offset = settings.DEFAULT_OFFSET_BETWEEN_RENTALS
        # get all "defect" status for this type
        object_status = RentalObjectStatus.objects.all().filter(from_date__lte=until_date, until_date__gte=from_date,
                                                                rentable=False, rental_object__in=RentalObject.objects.filter(type=pk))
        # remove all objects with an status from objects
        objects = RentalObject.objects.all().filter(
            type=pk).exclude(rentable=False).exclude(rentalobjectstatus__in=object_status)
        # exclude reservations that are already related to an rental also exclude them from counting if they are canceled
        reservations = Reservation.objects.filter(
            objecttype_id=pk, reserved_from__lte=until_date.date(), reserved_until__gte=from_date.date()).exclude(rental__in=Rental.objects.filter(rented_object__type=pk)).exclude(canceled__isnull=False)
        rentals = Rental.objects.filter(
            rented_object__in=objects, handed_out_at__lte=until_date)
        rentals = [r for r in rentals if r.extended_until() <= from_date.date()]
        count = len(objects)

        # give reservations + rentals them common keys for the dates
        normalized_list = [{**model_to_dict(x), 'from_date': x.handed_out_at.date(
        ), 'until_date': x.extended_until()} for x in rentals]
        # normalized_list = [ for x in reservations]
        for reservation in reservations:
            for _ in range(reservation.count):
                normalized_list.append(
                    {**model_to_dict(reservation), 'from_date': reservation.reserved_from, 'until_date': reservation.reserved_until})
        ret = {}
        max_value = 0
        for day_diff in range(delta.days+1):
            current_date = (from_date + timedelta(days=day_diff)).date()
            temp_value = 0
            for blocked_timerange in normalized_list:
                # calculate offset
                until_date_with_offset = (
                    blocked_timerange['until_date']+offset)
                if until_date_with_offset.isoweekday() != settings.DEFAULT_LENTING_DAY_OF_WEEK:
                    # since weekday is not a Lenting day we extend the "occupied/lended" state until the next lenting day
                    until_date_with_offset += timedelta(days=7-abs(
                        until_date_with_offset.isoweekday()-settings.DEFAULT_LENTING_DAY_OF_WEEK))
                if blocked_timerange['from_date'] <= current_date < blocked_timerange['until_date'] + offset:
                    temp_value += 1
            max_value = temp_value if temp_value > max_value else max_value
            ret[str(current_date)] = count-temp_value
        ret['available'] = count-max_value
        return ret

    def max_rent_duration(pk, prio: Priority):
        object_type = RentalObjectType.objects.get(id=pk)
        user_priority = prio
        if MaxRentDuration.objects.filter(
                prio=prio, rental_object_type=object_type).exists():
            instance = MaxRentDuration.objects.get(
                prio=user_priority, rental_object_type=object_type)
        elif MaxRentDuration.objects.filter(
                rental_object_type=object_type, prio__prio__gte=user_priority.prio).order_by('prio__prio').exists():
            # fallback to default duration
            instance = MaxRentDuration.objects.filter(
                rental_object_type=object_type, prio__prio__gt=user_priority.prio).order_by('prio__prio').first()
        else:
            # fallback fallback to 1 week
            instance = {
                'prio': None, 'rental_object_type': object_type, 'duration': timedelta(weeks=1)}

        return instance



class RentalObject(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_identifier', fields=[
                                    'type', 'internal_identifier'])
        ]
    type = models.ForeignKey(
        RentalObjectType, on_delete=models.CASCADE, related_name='rentalobjects')
    # if the object also got a external identifier e.g. a department uses its own identifiers but the objects also got a inventory number of the company
    inventory_number = models.CharField(max_length=100, null=True, blank=True)
    # maybe broken so it shouldnt be rentable
    rentable = models.BooleanField(default=True)
    # together with prefix_identifier from type class the short internal identifier e.g. LZ1
    internal_identifier = models.IntegerField()

    def __str__(self) -> str:
        return self.type.name + " " + str(self.type.prefix_identifier) + str(self.internal_identifier)


class RentalObjectStatus(models.Model):
    """
    A Status to prevent a Rentalobject to be rent. for example planned maintenance. defaults to now until infinity.
    """
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(from_date__lte=models.F('until_date')),
                name="object_status_enforce_from_date_lte_until_date"
            )
        ]
    rental_object = models.ForeignKey(
        RentalObject, verbose_name="Rentalobject", on_delete=models.CASCADE)
    reason = models.TextField(default="defekt")
    from_date = models.DateField(default=timezone.now)
    until_date = models.DateField(default=datetime.max)
    rentable = models.BooleanField(default=False)

    def __str__(self) -> str:
        return str(self.rental_object.__str__()) + " status"


class Reservation(models.Model):
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(reserved_from__lte=models.F('reserved_until')),
                name="reservation_reserved_from_date_lte_reserved_until"
            )
        ]
    reserver = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='reserver')
    reserved_at = models.DateTimeField(auto_now_add=True)
    reserved_from = models.DateField()
    reserved_until = models.DateField()
    objecttype = models.ForeignKey(RentalObjectType, on_delete=models.CASCADE)
    operation_number = models.BigIntegerField()
    count = models.PositiveSmallIntegerField()
    canceled = models.DateTimeField(null=True, blank=True, default=None)
    notified = models.DateTimeField(null=True, blank=True, default=None)

    def __str__(self) -> str:
        return 'reservation: ' + str(self.operation_number)


class Rental(models.Model):
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    models.Q(handed_out_at__lte=models.F('received_back_at')) | models.Q(received_back_at__isnull=True)),
                name="rental_handed_out_lte_received_date"
            ),
        ]
    rented_object = models.ForeignKey(RentalObject, on_delete=models.CASCADE)
    lender = models.ForeignKey(User, blank=True, null=True,
                               default=None, on_delete=models.CASCADE, related_name='lender')
    return_processor = models.ForeignKey(User, blank=True, null=True, default=None, on_delete=models.CASCADE,
                                         related_name='return_processor', verbose_name='person who processes the return')
    rental_number = models.BigIntegerField()
    handed_out_at = models.DateTimeField(null=True, blank=True)
    received_back_at = models.DateTimeField(
        null=True, default=None, blank=True)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    notified = models.DateTimeField(null=True, blank=True, default=None)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None) -> None:
        # check if the inserted rented object is the same type as the type required from the reservation
        if self.reservation.objecttype.pk != self.rented_object.type.pk:
            raise ValueError("Reservationtype and type of inserted rented object have to be equal")
        return super().save(force_insert, force_update, using, update_fields)

    def extended_until(self) -> date:
        currentend = self.reservation.reserved_until
        if self.extension_set.count()>0:
            currentend = self.extension_set.order_by('-extended_until').first().extended_until
        return currentend     

    def __str__(self) -> str:
        return 'Rental: ' + str(self.rental_number)
    
class Extension(models.Model):
    """
    model to save extensions more verbose
    """
    extended_from = models.DateField(default=None, null=False)
    extended_until = models.DateField(default=None, null=False)
    extended_at = models.DateTimeField(default=timezone.now, null=False)
    extended_by = models.ForeignKey(User, on_delete=models.CASCADE)
    extended_rental = models.ForeignKey(Rental, on_delete=models.CASCADE)

class OnPremiseBlockedTimes(models.Model):
    """
    To block specific days e.g. someone is ill
    """
    starttime = models.DateTimeField(default=None, null=False)
    endtime = models.DateTimeField(default=None, null=False)


class OnPremiseWorkplace(models.Model):
    """
    Workplace on premise, maybe create many to many relationship to objects(For objects that can be used on premise)
    """
    name = models.CharField(max_length=100)
    description = models.TextField(default='')
    shortdescription = models.TextField(default='')
    displayed = models.BooleanField(default=True)
    image = models.ImageField(default='nopicture.png')
    exclusions = models.ManyToManyField('OnPremiseWorkplace', blank=True)
    #suggested_types = models.ManyToManyField(RentalObjectType)


class OnPremiseBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    showed_up = models.BooleanField(blank=True, default=False)
    workplace = models.ForeignKey(OnPremiseWorkplace, on_delete=models.CASCADE)
    slot_start = models.DateTimeField()
    slot_end = models.DateTimeField()
    comment = models.TextField(blank=True, default="")
    canceled = models.DateTimeField(blank=True, default=None, null=True)
    #needed_types = models.ManyToManyField(RentalObjectType)


class OnPremiseWorkplaceStatus(models.Model):
    """
    Disable workplace for a Period of time
    """
    workplace = models.ForeignKey(OnPremiseWorkplace, on_delete=models.CASCADE, related_name="status")
    from_date = models.DateTimeField()
    until_date = models.DateTimeField()
    reason = models.TextField()
    


class Settings(models.Model):
    """
    for general dynamic Settings like general lenting day and rocketchat url
    """
    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='unique_settings',
                fields=['type']
            )
        ]
    type = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    public = models.BooleanField()

    def __str__(self) -> str:
        return self.type


class Text(models.Model):
    name = models.CharField(max_length=100)
    content = models.TextField(default="", null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='Unique_text_slug',
                fields=['name']
            )
        ]
        verbose_name = ("Text")
        verbose_name_plural = ("texts")

    def __str__(self):
        return self.name


class Suggestion(models.Model):
    """
    for suggestions which objects should be rented together
    """
    suggestion = models.ForeignKey(
        RentalObjectType, on_delete=models.CASCADE, related_name='suggestion')
    suggestion_for = models.ForeignKey(
        RentalObjectType, on_delete=models.CASCADE, related_name='suggestion_for')
    description = models.TextField(verbose_name="Description, why is this a suggestion for the other one?", default="", blank=True)

class PasswordReset(models.Model):
    """
    Saves the data for a password reset.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hash = models.CharField(max_length=1024)
    creation_date = models.DateTimeField(default=timezone.now)

class MaxRentDuration(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='unique_prio_type',
                fields=['prio', 'rental_object_type']
            )
        ]
    prio = models.ForeignKey(Priority, on_delete=models.CASCADE)
    rental_object_type = models.ForeignKey(
        RentalObjectType, on_delete=models.CASCADE)
    duration = models.DurationField()


class Files(models.Model):
    file = models.FileField(default="docxtemplate.docx")
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class OauthVerificationProcess(models.Model):
    # since we do not need the Process if a user gets deleted 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_code = models.CharField(max_length=100)
    device_code = models.CharField(max_length=100) 
    ping_interval = models.DurationField(default=timedelta(seconds=5))
    last_ping = models.DateTimeField(null=True, blank=True, verbose_name="last time the server got pinged")
    verification_process_expires = models.DateTimeField()
    target = models.CharField(max_length=100,verbose_name="id a provider", blank=True)
    access_token = models.CharField(max_length=130,null=True, blank=True, default=None)
    access_token_exipiry = models.DateTimeField(null=True, blank=True, default=None)
    refresh_token = models.CharField(max_length=130, null=True, blank=True)
    faculty = models.CharField(max_length=100)


# class Notification(models.Model):
#     """
#     for planned notificaitons
#     """
#     type = models.CharField(max_length=100, default='email')
#     receiver = models.CharField(max_length=255)
#     subject = models.CharField(max_length=255)
#     content = models.TextField()
#     added_at = models.DateTimeField(auto_now_add=True)
#     sent_at = models.DateTimeField(null=True)
#     send_at = models.DateTimeField(default=timezone.now)
