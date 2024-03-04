import hashlib
from django.utils.crypto import get_random_string
from datetime import datetime, timedelta
from django.contrib.auth import login
from django.contrib.auth.models import User, Group, Permission
from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template
from django.template.loader import render_to_string
from django.forms.models import model_to_dict
from django.core.exceptions import FieldError
from django.db.models import Max, Q, F
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse, FileResponse
from django.shortcuts import redirect
from django.db import IntegrityError
import os

from rest_framework import status
from rest_framework.request import Request
from rest_framework import viewsets, renderers
from rest_framework import permissions
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework.decorators import api_view, action, authentication_classes, permission_classes
from rest_framework.views import exception_handler


from knox.views import LoginView as KnoxLoginView
from knox.auth import TokenAuthentication

from .serializers import CategorySerializer, UserSerializer, RentalObjectSerializer, UserCreationSerializer, GroupSerializer, KnowLoginUserSerializer, RentalObjectTypeSerializer, ReservationSerializer, RentalSerializer, TagSerializer, TextSerializer
from .permissions import UserPermission, GroupPermission
from api import permissions as customPermissions
from api import serializers

from base.models import RentalObject, RentalObjectType, Category, Reservation, Rental, Profile, Tag, Text
from base import models

from docxtpl import DocxTemplate
import io

import requests

# Allow to Login with Basic auth for testing purposes
import logging
import sys
import re

logger = logging.getLogger(name="django")

def integrity_error_exception_handler(exc, context):
    """
    custom errorhandler. Translates e.g. internal model errors to correct statuscodes and errormessages.
    returns drf default errorresponse if it is a known error
    returns a custom errorresponse if it is a unkown error
    """
    response = exception_handler(exc, context)

    if isinstance(exc, IntegrityError) and not response:
        # check if it is a key duplication error
        matches = re.findall(r"Key \((.+)\)=\((.+)\) already exists",str(exc))
        text = 'ein Datenbankobject mit diesem key existiert bereits'
        if len(matches)==1 and len(matches[0])==2 and matches[0][0]=="prefix_identifier":
            text = "Es wurde bereits ein Objekt mit dem Präfix Identifier: " + matches[0][1] + " erstellt. Bitte wähle einen anderen Präfix."
        response = Response({'detail': text}, status=status.HTTP_400_BAD_REQUEST)

    return response

class LoginView(KnoxLoginView):
    """
    Loginview returns a Authtoken for the user to login
    """
    permission_classes = [permissions.AllowAny, ]

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super(LoginView, self).post(request, format=None)

    def get_user_serializer_class(self):
        return KnowLoginUserSerializer


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def checkCredentials(request: Request):
    """
    Api Endpoint to check if credentials are valid
    """
    serializer = serializers.KnowLoginUserSerializer(request.user)
    return (Response(serializer.data, status=200))


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [UserPermission]

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def passwordreset(self, request:Request):
        if 'username' in request.data and 'email' in request.data:
            usermodel = models.User.objects.filter(username=request.data['username'], email=request.data['email'])
            if usermodel.count()==1:
                logger.info("Nutzer gefunden Resetlink wird generiert")
                usermodel = usermodel[0]
                hash = hashlib.sha256(
                    (str(timezone.now()) + get_random_string(length=256)).encode("utf-8")).hexdigest()
                models.PasswordReset.objects.create(user=usermodel, hash=hash)
                link=settings.FRONTEND_HOST + 'account/passwordreset?hash='+ hash
                email_text = render_to_string('passwordreset.html',{'link':link})
                send_mail(subject="Passwordreset", message=email_text, html_message=email_text,
                        from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[request.data['email']])
            else:
                logger.info(f"Es wurden {usermodel.count()} Accounts zu den Daten Email: {request.data['username']} und Nutzername: {request.data['email']} gefunden. Daher kann kein Reset Link gesendet werden")
        return Response(data={'abs':'abs'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def passwordreset_confirm (self, request:Request):
        # check if a Passwordresetprozess for this hash exists
        try:
            reset_model = models.PasswordReset.objects.get(hash=request.data['hash'])
        except:
            return Response(data={'detail': "Kein Passwortresetprozess gefunden"}, status=status.HTTP_400_BAD_REQUEST)
        # check if link is still valid
        if reset_model.creation_date < timezone.now()-timedelta(days=1):
            reset_model.delete()
            return Response(data={'detail': "Passwortreset ist abgelaufen"}, status=status.HTTP_400_BAD_REQUEST)
        password = request.data['password']
        if len(password) < 8:
            return Response(data={'detail': "Das Passwort entspricht nicht den Vorgaben"}, status=status.HTTP_400_BAD_REQUEST)
        user_model = reset_model.user
        user_model.set_password(password)
        user_model.save()
        reset_model.delete()
        return Response("Das Passwort wurde erfolgreich geändert")

    @action(detail=True, methods=['post'], url_path="toggle_permission", permission_classes=[customPermissions.UserPermission])
    def toggle_permission(self, request:Request, pk=None):
        user = User.objects.get(pk=pk)
        if 'permission' in request.data:
            permission_whitelist = ['lending_access', 'inventory_editing']
            if request.data['permission'] in permission_whitelist:
                permission = Permission.objects.get(codename__contains=request.data['permission'])
                if user.user_permissions.contains(permission):
                    user.user_permissions.remove(permission)
                else:
                    user.user_permissions.add(permission)
                #user.user_permissions.add(permission)

        else:
            return Response("missing permission param", status=status.HTTP_400_BAD_REQUEST)
        user.refresh_from_db()
        return Response(self.get_serializer_class()(user).data)

    @action(detail=False, methods=['post'], url_path="oauth/verify", permission_classes=[permissions.IsAuthenticated])
    def verify_with_oauth(self, request: Request):
        """
        if no verification process has been startet yet, fetch user and device code from the endpoint and return the verification url for the user.
        please call /api/users/oauth/token to check if the user already finished the process
        """
        process = models.OauthVerificationProcess.objects.filter(
            user=request.user)
        if len(process) > 0:
            if process.first().access_token == None:
                return Response({"url": settings.OAUTH_CLIENTS['oauth']['OAUTH_VERIFICATION_URL'] + process.first().user_code, "max_refresh_interval": process.first().ping_interval.seconds})
            else:
                # delete process expired restart process by deleting it
                if process.first().access_token != None and process.first().verification_process_expires < timezone.now():
                    process.first().delete()
                else:
                    return Response({"url": "", "max_refresh_interval": 0})
        rsp = requests.post(settings.OAUTH_CLIENTS['oauth']['OAUTH_AUTHORIZATION_CODE_URL'], data={
                            "client_id": settings.OAUTH_CLIENTS['oauth']['client_id'], 'scope': settings.OAUTH_CLIENTS['oauth']['scope']})

        rsp = rsp.json()
        device_code = rsp['device_code']
        user_code = rsp['user_code']
        url = settings.OAUTH_CLIENTS['oauth']['OAUTH_VERIFICATION_URL'] + user_code
        verifaction_process = models.OauthVerificationProcess.objects.create(
            device_code=device_code,
            user_code=user_code,
            ping_interval=timedelta(seconds=rsp['interval']),
            verification_process_expires=timezone.now(
            ) + timedelta(seconds=rsp['expires_in']),
            user=request.user)
        verifaction_process.save()

        # logger.info(state)
        return Response({"url": url, "max_refresh_interval": rsp['interval']})

    @action(detail=False, methods=['post'], url_path="oauth/token", permission_classes=[permissions.IsAuthenticated])
    def get_access_token(self, request: Request):
        """
        this function calls the OAUTH-Endpoint and fetches the accesstoken if none is already present, if one is present the api is called and the status is verfied and written  to the profile and the priority is set to a verified state
        """
        # first we check if there is a process for this account
        process = models.OauthVerificationProcess.objects.filter(
            user=request.user)
        if len(process) == 0:
            return Response("Expired. Please start the verification process by calling /oauth/verify", status=status.HTTP_400_BAD_REQUEST)
        process = process.first()
        if process.access_token == None and process.verification_process_expires < timezone.now():
            # check if the verification process is expired and delete it if it is
            process.delete()
            return Response("verificationsprocess expired, please restart the process", status=status.HTTP_400_BAD_REQUEST)

        if (process.last_ping != None and process.last_ping+process.ping_interval > timezone.now()):
            # we prevent the external API from being called to often, therefore we limit it ourselves
            return Response({'status': "error", "description": "Please slow down, we are not allowed to ping the auth server that often"}, status=status.HTTP_400_BAD_REQUEST)
        data = {"verified": False}
        if process.access_token == None:
            # if the current process contains a access_token the verification process is done if not we have to call the api and ask if the user endet his/her verification
            process.last_ping = timezone.now()
            process.save()
            accesstokenrsp = requests.post(settings.OAUTH_CLIENTS['oauth']['OAUTH_ACCESS_TOKEN_URL'], data={
                "client_id": settings.OAUTH_CLIENTS['oauth']['client_id'], "code": process.device_code, "grant_type": "device"})
            data = accesstokenrsp.json()
            if data['access_token'] != None:
                process.access_token = data['access_token']
                process.refresh_token = data['refresh_token']
                process.access_token_exipiry = timezone.now(
                ) + timedelta(seconds=data['expires_in'])
                process.save()
            process.refresh_from_db()
        if process.access_token != None and not request.user.profile.verified:
            # important part get data from api and update user profile and priorities accordingly.
            userdata = requests.get(
                settings.OAUTH_CLIENTS['oauth']['OAUTH_VERIFICATIONDATA_ENDPOINT']+process.access_token).json()
            if userdata["IsError"]:
                return Response("there was an error while calling the api. please write an message to us")
            # TODO TESTING REPLACE with correct api endpoint and faculty
            data_field = settings.OAUTH_CLIENTS['oauth']['OAUTH_DATA_KEY']
            if "Data" in userdata and data_field in userdata["Data"] and userdata["Data"][data_field] == settings.OAUTH_CLIENTS['oauth']['OAUTH_DATA_VALUE']:
                logger.debug("user: " + str(request.user.pk) +
                             " has been automatically verified")
                request.user.profile.verified = True
                request.user.profile.prio = models.Priority.objects.get(
                    prio=50, name__contains="automatically")
                request.user.profile.save()
            else:
                request.user.profile.automatically_verifiable = False
                request.user.profile.save()
                data = {"automatically_verifiable": False}
                logger.debug("user: " + str(request.user.pk) +
                             " couldn't be automatically verified. \n" + str(userdata))
        if request.user.profile.verified:
            data = {"verified": True}
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def email_validation(self, request: Request):
        """
        Endpoint to validate the register email against. validates the registered hash
        """
        hash = request.POST['hash']
        # to be able to deactivate accounts last login is checked
        for model in User.objects.all().filter(is_active=False, last_login__isnull=True):
            model_hash = hashlib.sha256(
                (str(model.date_joined) + model.username + settings.EMAIL_VALIDATION_HASH_SALT).encode("utf-8")).hexdigest()
            if model_hash == hash:
                model.is_active = True
                model.save()
                # User.objects.get(pk=model.id).update(is_active=True)
                return Response(data={'success': True, 'detail': "Die Email wurde erfolgreich validiert und man kann sich mit dem verbundenen Account einloggen."})
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'detail': "Der Link wurde entweder schon benutzt oder der Link ist falsch, bitte stelle sicher dass der Link richtig eingegeben wurde"})
        # {key:value for key, value in }

    def get_serializer_class(self):
        """
        use another serializer to reduce the amount of "magic"
        """
        if self.action == 'create':
            return UserCreationSerializer
        else:
            if self.request.user.has_perm("base.inventory_editing"):
                # response with all data
                return serializers.AdminUserSerializer
            return UserSerializer

    def create(self, request, *args, **kwargs):
        """
        use default implementation, but remove password from returned data and send email to user.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        data = serializer.data
        data['password'] = ''
        user = User.objects.get(pk=data['id'])
        if type(user) is not dict:
            templateData = model_to_dict(user)
        else:
            templateData = user
        templateData['frontend_host'] = settings.FRONTEND_HOST
        templateData['hash'] = hashlib.sha256(
            (str(templateData["date_joined"]) + templateData["username"] + settings.EMAIL_VALIDATION_HASH_SALT).encode("utf-8")).hexdigest()
        templateData['validation_link'] = f"{templateData['frontend_host']}validate/{templateData['hash']}"
        template = Template(models.Text.objects.filter(
            name='signup_mail').first().content.replace(r"%}}</p>", r"%}}").replace(r"<p>{{%", r"{{%"))
        message = template.render(Context(templateData))

        # TODO validate if mail has been send
        send_mail(subject="Registrierung", message=message, html_message=message,
                  from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[templateData['email']])
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [GroupPermission]


class RentalobjectViewSet(viewsets.ModelViewSet):
    queryset = RentalObject.objects.all().order_by('internal_identifier')
    serializer_class = RentalObjectSerializer
    # TODO assign rights
    permission_classes = [customPermissions.RentalObjectPermission]

    def get_queryset(self):
        queryset = RentalObject.objects.all()
        getdict = self.request.GET
        if 'type' in getdict:
            queryset = queryset.filter(type=getdict['type'])

        return queryset


class RentalobjectTypeViewSet(viewsets.ModelViewSet):
    queryset = RentalObjectType.objects.all()
    serializer_class = RentalObjectTypeSerializer
    permission_classes = [customPermissions.RentalObjectTypePermission]

    # TODO add Permission for admin with inv rights
    @action(detail=True, url_path="suggestions", methods=['GET', 'PATCH'], permission_classes=[permissions.IsAuthenticated])
    # we make it atomic to prevent loss of suggestions on error
    @transaction.atomic
    def suggestions_for_type(self, request: Request, pk=None):
        """
        return a list of suggestions for a specific type on get
        replaces the current list of suggestions for a specific type patch
        """
        if request.method == 'GET':
            suggestions = models.Suggestion.objects.filter(
                suggestion_for__pk=pk)
            serializer = serializers.SuggestionSerializer(
                suggestions, many=True)
            return Response(serializer.data)
        else:
            data = request.data
            data = list(map(lambda x: {**x, "suggestion_for": pk}, data))
            models.Suggestion.objects.filter(suggestion_for__pk=pk).delete()
            serializer = serializers.SuggestionSerializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            # check for duplicates and error if one exists
            seen = set()
            for sugg in serializer.data:
                if sugg['suggestion'] in seen:
                    raise serializers.serializers.ValidationError(
                        "Duplicated suggestion")
                seen.add(sugg['suggestion'])

            data = serializer.save()
            return Response(serializers.SuggestionSerializer(data, many=True).data)

    @action(detail=True, url_path="duration", methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def max_duration(self, request: Request, pk=None):
        """
        returns the max Duration for a user
        """
        user_priority = request.user.profile.prio
        instance = models.RentalObjectType.max_rent_duration(
            pk=pk, prio=user_priority)

        serializer = serializers.MaxRentDurationSerializer(instance)
        return Response(serializer.data)

    @action(detail=True, url_path="freeobjects", methods=['GET'])
    def currently_free_objects(self, request: Request, pk=None):
        object_status = models.RentalObjectStatus.objects.all().filter(from_date__lte=timezone.now(), until_date__gte=timezone.now(),
                                                                       rentable=False, rental_object__in=RentalObject.objects.filter(type=pk))
        queryset = models.RentalObject.objects.filter(
            type=pk, rentable=True).exclude(rentalobjectstatus__in=object_status)
        result = []
        for rental_object in queryset:
            query_res = rental_object.rental_set.filter(Q(
                Q(received_back_at__isnull=True), Q(Q(handed_out_at__lte=timezone.now())|Q(handed_out_at__isnull=True))))
            if len(query_res) == 0:
                data = model_to_dict(rental_object)
                result.append(data)
        return Response(result)

    @action(detail=True, url_path="available", methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def available_object(self, request: Request, pk=None):
        """
        takes two arguments a start date and an end date end calculates if that object is available around that time
        """
        if not models.RentalObjectType.objects.all().filter(id=pk).exists():
            raise models.RentalObjectType.DoesNotExist
        if not 'from_date' in request.query_params:
            raise FieldError("from_date query param is missing")
        if not 'until_date' in request.query_params:
            raise FieldError("until_data query param is missing")

        from_date = datetime.strptime(
            request.query_params['from_date'], "%Y-%m-%d").replace(tzinfo=timezone.get_current_timezone())
        until_date = datetime.strptime(
            request.query_params['until_date'], "%Y-%m-%d").replace(tzinfo=timezone.get_current_timezone())
        ret = models.RentalObjectType.available(
            pk=pk, until_date=until_date, from_date=from_date)
        return Response(data=ret)

    @action(detail=False, url_path="available", methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def available_objects(self, request: Request):
        """
        this function does the same as available_object only for querysets returns all objects available around that time
        """
        # TODO allow the supply of a specific set of types
        queryset = self.get_queryset().filter(visible=True)
        data = {}
        for object_type in queryset:
            data[object_type.id] = self.available_object(
                request=request, pk=object_type.id).data

        return Response(data)

    def get_queryset(self):
        queryset = RentalObjectType.objects.all().order_by('category', 'name')
        getdict = self.request.GET
        if 'visible' in getdict and getdict['visible'] in ['true', 'True']:
            queryset = queryset.filter(visible=True)
        return queryset


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # TODO assign rights
    permission_classes = [customPermissions.CategoryPermission]


class ReservationViewSet(viewsets.ModelViewSet):
    """
    Limit returned objects by open, from and until get requests
    """

    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    # TODO assign rights
    permission_classes = [customPermissions.ReservationPermission]

    def get_serializer_class(self):
        return serializers.ReservationAdminSerializer if self.request.user.is_staff else serializers.ReservationSerializer

    def get_queryset(self):
        queryset = Reservation.objects.all()
        getdict = self.request.GET
        if 'reserved_from' in getdict:
            # we fetch all starting after that
            queryset = queryset.filter(
                reserved_from__gte=getdict['reserved_from'])
        if 'reserved_until' in getdict:
            queryset = queryset.filter(
                reserved_from__lte=getdict['reserved_until'])
        if 'open' in getdict:
            if getdict['open'] in ['true', 'True']:
                # remove all reservations that already got a corresponding rental
                queryset = queryset.exclude(rental__handed_out_at__isnull=False)
        if 'unique' in getdict:
            if getdict['unique'] in ['true', 'True']:
                queryset = queryset.distinct('operation_number')
        if 'operation_number' in getdict:
            queryset = queryset.filter(
                operation_number=getdict['operation_number'])
        if "self" in self.request.GET and self.request.GET["self"] in ["true", "True"]:
            # query only own rentals (necessary for users without special rights)
            queryset = queryset.filter(reserver=self.request.user.profile)
        if 'canceled' in getdict:
            if getdict['canceled'] in ['false', 'False']:
                queryset = queryset.filter(canceled__isnull=True)
        return queryset
    
    @action(detail=True, url_path="selectedobjects", methods=['GET'])
    def currently_selected_objects(self, request: Request, pk=None):
        queryset = models.RentalObject.objects.filter(rental__reservation=pk)
        result = []
        for rental_object in queryset:
            data = model_to_dict(rental_object)
            result.append(data)
        return Response(result)

    @action(detail=True, methods=['POST'], url_path="cancel", permission_classes=[permissions.IsAuthenticated])
    def cancel_reservation(self, request: Request, pk=None):
        reservation = Reservation.objects.get(pk=pk)
        if request.user != reservation.reserver.user and not request.user.is_staff:
            return Response("Not allowed", status=status.HTTP_400_BAD_REQUEST)
        if reservation.canceled != None:
            return Response("already canceled", status=status.HTTP_400_BAD_REQUEST)
        reservation.canceled = timezone.now()
        reservation.save()
        reservation.rental_set.all().delete()
        serializer = ReservationSerializer(reservation)
        template_data = serializer.data
        template = Template(models.Text.objects.filter(
            name='reservation_cancel_mail').first().content)
        message = template.render(Context(template_data))
        send_mail(subject="Stornierung deiner Reservierung", message=message, html_message=message,
                  from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[reservation.reserver.user.email])

        return Response(serializer.data)

    @action(detail=False, methods=['POST'], url_path="bulk", permission_classes=[permissions.IsAuthenticated])
    def bulk_create(self, request: Request):
        """
        create reservations from a list of reservation candidates
        """
        data = request.data['data']
        if models.Reservation.objects.all().exists():
            operation_number = models.Reservation.objects.aggregate(
                Max('operation_number'))['operation_number__max']+1
        else:
            operation_number = 1

        response_data = []
        for reservation in data:
            if reservation['count'] > models.RentalObjectType.available(reservation['objecttype'], datetime.strptime(reservation['reserved_from'], "%Y-%m-%d").replace(tzinfo=timezone.get_current_timezone()), datetime.strptime(reservation['reserved_until'], "%Y-%m-%d").replace(tzinfo=timezone.get_current_timezone()))['available']:
                return Response({'data': 'not enough objects available'}, status=status.HTTP_400_BAD_REQUEST)
        template_data = {"reservations": []}
        for reservation in data:
            # merge reservations of the same type and not aleardy rented
            if models.Reservation.objects.filter(
                    reserved_from=reservation["reserved_from"],
                    reserved_until=reservation["reserved_until"],
                    objecttype=reservation["objecttype"],
                    reserver=request.user.profile.pk).exclude(
                        rental__in=Rental.objects.filter(rented_object__type=reservation['objecttype'])).exclude(canceled__isnull=False).count() == 0:
                reservation['operation_number'] = operation_number
                reservation['reserver'] = request.user.profile.pk
                serializer = serializers.BulkReservationSerializer(
                    data=reservation)
                serializer.is_valid(raise_exception=True)
                template_data["reservations"].append(serializer.validated_data)
                serializer.save()
            else:
                count = reservation['count']
                reservation = models.Reservation.objects.get(
                    reserved_from=reservation["reserved_from"], reserved_until=reservation["reserved_until"], objecttype=reservation["objecttype"], reserver=request.user.profile.pk, canceled__isnull=True)
                reservation.count += count
                reservation.save()
                serializer = serializers.BulkReservationSerializer(reservation)

            response_data.append(serializer.data)
        template_data = {**template_data,
                         "lenting_start_hour": models.Settings.objects.get(type="lenting_start_hour").value,
                         "lenting_end_hour": models.Settings.objects.get(type="lenting_end_hour").value,
                         "returning_start_hour": models.Settings.objects.get(type="returning_start_hour").value,
                         "returning_end_hour": models.Settings.objects.get(type="returning_end_hour").value, }
        template = Template(models.Text.objects.filter(
            name='reservation_confirmation_mail').first().content.replace(r"%}}</p>", r"%}}").replace(r"<p>{{%", r"{{%"))
        message = template.render(Context(template_data))
        if len(template_data['reservations']) > 0:
            send_mail(subject="Deine Reservierung", message=message, html_message=message,
                      from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[template_data['reservations'][0]["reserver"].user.email])
        return Response(data={'data': response_data})

    @ action(detail=False, methods=['POST'], url_path="download_form", permission_classes=[permissions.IsAuthenticated])
    def download_form(self, request: Request):
        """
        expecting data in [{id, reserver: {'user': {first_name:string, last_name:string, email:string} }, objecttype: {name:string, prefix_identifier:string}, slectedObjects: [pk:int], reserved_from: %Y-%m-%d :string, reserved_until:string }] for each type an instance
        """
        logger.info(f"Downloading rental form for reservations: {list(map(lambda x:x['id'], request.data))}")
        context = {'rented_items': [], 'reserver': {}}
        for reservation in request.data:
            context['reserver']['last_name'] = reservation['reserver']['user']['last_name']
            context['reserver']['first_name'] = reservation['reserver']['user']['first_name']
            context['reserver']['email'] = reservation['reserver']['user']['email']
            context['rented_items'].append({'operation_number':reservation['operation_number'],'reserved_from': reservation['reserved_from'], 'reserved_until': reservation['reserved_until'], 'count': reservation['count'], 'name': reservation['objecttype']['name'], 'identifier': ",".join(
                [reservation['objecttype']['prefix_identifier'] + str(models.RentalObject.objects.get(pk=thing).internal_identifier) for thing in reservation['selectedObjects']])})
        filepath = models.Files.objects.get(name='rental_form').file.path
        doc = DocxTemplate(filepath)
        doc.render(context=context)
        file = io.BytesIO()
        doc.save(file)
        # we have to use djangos Response class here because the DRF's class does weird stuff
        return HttpResponse(file.getvalue(), content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


class RentalViewSet(viewsets.ModelViewSet):
    queryset = Rental.objects.all()
    serializer_class = RentalSerializer
    permission_classes = [customPermissions.RentalPermission]

    def get_queryset(self):
        queryset = models.Rental.objects.all()
        if self.request.user.is_staff:
            queryset = queryset
        else:
            queryset = queryset.filter(reservation__reserver=self.request.user.profile)
        if "open" in self.request.GET and self.request.GET["open"] in ["true", "True"]:
            queryset = queryset.filter(received_back_at__isnull=True, handed_out_at__isnull=False)

        if "self" in self.request.GET and self.request.GET["self"] in ["true", "True"]:
            # query only own rentals (necessary for users without special rights)
            queryset = queryset.filter(
                reservation__reserver=self.request.user.profile, handed_out_at__isnull=False)
        if "reservation" in self.request.GET:
            queryset = queryset.filter(reservation=int(self.request.GET["reservation"]))
        return queryset

    @ action(detail=True, methods=['POST'], url_path="extend", permission_classes=[permissions.IsAuthenticated])
    @transaction.atomic
    def extend_rental(self, request: Request, pk=None):
        """
        extends the rental by one week
        """
        rental = models.Rental.objects.get(pk=pk)
        serializer = serializers.RentalSerializer(
            rental, context={'request': request})
        if serializer.data['extendable']:
            daydiff = (serializer.data['extended_until']-timezone.now().date()).days
            if (not request.user.is_staff) and (daydiff >= 2 or daydiff < 0):
                raise APIException(f"Daydiff = {daydiff}, only 1 and 2 are possible values", code=status.HTTP_400_BAD_REQUEST)
            elif (daydiff >= 9 or daydiff < 0):
                raise APIException(f"Daydiff = {daydiff}, only values between 9 and 1 are possible values", code=status.HTTP_400_BAD_REQUEST)
            else:
                models.Extension.objects.create(extended_by=request.user, extended_from=rental.extended_until(), extended_until=serializer.data['extended_until']+timedelta(weeks=1), extended_rental=rental)
                rental.notified = None
                rental.save()
                serializer = serializers.RentalSerializer(
                    rental, context={'request': request})
                return Response(serializer.data)
        else:
            return APIException("nicht verlängerbar", code=status.HTTP_400_BAD_REQUEST)

    @ action(detail=False, methods=['POST'], url_path="bulk", permission_classes=[permissions.IsAuthenticated])
    def bulk_rental_creation(self, request: Request):
        """
        Takes a list of reservations with a list of slectedObjects each to create collected rentals to be handed out
        """
        if models.Rental.objects.all().exists():
            rental_number = models.Rental.objects.aggregate(
                Max('rental_number'))['rental_number__max']+1
        else:
            rental_number = 1
        for reservation in request.data:
            logger.info(reservation)
            reservation_model = models.Reservation.objects.get(pk=reservation['id'])
            # remove all Rentals that are on this rental 
            reservation_model.rental_set.exclude(rented_object__in=reservation['selectedObjects']).delete()
            already_saved_rental_objects = reservation_model.rental_set
            for selected in reservation['selectedObjects']:
                if already_saved_rental_objects.filter(rented_object__pk=selected):
                    continue
                rental_object = models.RentalObject.objects.get(pk=selected)
                models.Rental.objects.create(reservation=reservation_model,rented_object=rental_object, rental_number=rental_number)
        reservation_model.refresh_from_db()
        serializer = serializers.ReservationSerializer(reservation_model)
        return Response(serializer.data)
        template_data = []
        ret_data = []
        for reservation in request.data:
            for index in range(reservation['count']):
                rental = {}
                rental['rented_object'] = reservation['selectedObjects'][index]
                rental['lender'] = request.user.pk
                rental['rental_number'] = rental_number
                rental['handed_out_at'] = timezone.now()
                rental['reservation'] = reservation['id']
                # we need an own serializer since reservation needs to be read only on the other serializer
                serializer = serializers.RentalCreateSerializer(data=rental)
                serializer.is_valid(raise_exception=True)
                template_data.append(serializer.validated_data)
                serializer.save()
                ret_data.append(serializer.data)
        template = Template(models.Text.objects.filter(
            name='rental_confirmation_mail').first().content.replace(r"%}}</p>", r"%}}").replace(r"<p>{{%", r"{{%"))
        message = template.render(Context({'rentals': template_data}))
        send_mail(subject="Dein Ausleihvorgang", message=message, html_message=message,
                  from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[template_data[0]['reservation'].reserver.user.email])
        return Response(ret_data)
    @ action(detail=False, methods=['POST'], url_path="bulkhandout", permission_classes=[permissions.IsAuthenticated])
    def bulk_rental_handout(self, request: Request):
        """
        checks if all rentals are correct for a list of reservationIDs and commits them
        """
        with transaction.atomic():
            for reservation in models.Reservation.objects.filter(pk__in=request.data["reservations"]):
                rental_set = reservation.rental_set
                if rental_set.all().count() != reservation.count:
                    raise ValueError("The number of rented objects is unequal to the number of reserved objects")
                rental_set.all().update(handed_out_at= timezone.now())
                #TODO send email on handout
        return Response()

    @ action(detail=False, methods=['POST'], url_path="return", permission_classes=[permissions.IsAuthenticated])
    def bulk_return(self, request: Request):
        """
        takes a list of rental ids and ends their rental duration to now.
        @return either return 400 if it does not find some rentals. otherwise returns number of changed objects
        """
        queryset = models.Rental.objects.filter(
            pk__in=request.data, received_back_at=None)
        if len(queryset) != len(request.data):
            return Response("couldn't find some of those rentals", status=status.HTTP_400_BAD_REQUEST)
        updated = queryset.update(received_back_at=timezone.now())
        return Response(updated)


class TextViewSet(viewsets.ModelViewSet):
    queryset = Text.objects.all()
    serializer_class = TextSerializer
    permission_classes = [customPermissions.TextPermission]

    def get_queryset(self):
        queryset = Text.objects.all()
        getdict = self.request.GET
        if 'names' in getdict:
            queryset = queryset.filter(name__in=getdict['names'].split(","))
        return queryset


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    # TODO assign rights everyone list, retrieve, post patch and put only with permission and logged in
    permission_classes = [customPermissions.TagPermission]


class PriorityViewSet(viewsets.ModelViewSet):
    queryset = models.Priority.objects.all()
    serializer_class = serializers.PrioritySerializer
    permission_classes = [customPermissions.PriorityPermission]


class SettingsViewSet(viewsets.ModelViewSet):
    queryset = models.Settings.objects.filter(public=True)
    serializer_class = serializers.SettingsSerializer
    permission_classes = [customPermissions.SettingsPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'name' in self.request.GET:
            queryset = queryset.filter(name=self.request.GET['name'])
        return queryset


class MaxRentDurationViewSet(viewsets.ModelViewSet):
    queryset = models.MaxRentDuration.objects.all()
    serializer_class = serializers.MaxRentDurationSerializer
    permission_classes = [customPermissions.MaxRentDurationPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        getdict = self.request.GET
        if 'object_type' in getdict:
            queryset = queryset.filter(
                rental_object_type=getdict['object_type'])
        return queryset

class FilesViewSet(viewsets.ModelViewSet):
    queryset = models.Files.objects.all()
    serializer_class = serializers.FilesSerializer
    permission_classes = [customPermissions.FilesPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'name' in self.request.GET:
            queryset.filter(name=self.request.GET['name'])
        return queryset

    @ action(detail=False, methods=['POST'], url_path="rental_form_template", permission_classes=[permissions.IsAdminUser])
    def update_rental_form_set(self, request: Request):
        data = request.data
        instance = models.Files.objects.get(name='rental_form')
        instance.file = data['file']
        data = serializers.FilesSerializer(
            instance=instance).is_valid(raise_exception=True).save()
        return Response(data=data)

    @ action(detail=False, methods=['GET'], url_path="download", permission_classes=[permissions.IsAdminUser])
    def download(self, request: Request):
        if ('name' not in request.GET):
            return HttpResponse("missing 'name' query param", status.HTTP_400_BAD_REQUEST)
        instance = self.queryset.filter(name=request.GET['name']).first()
        file = instance.file.open()
        return HttpResponse(file, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = models.Profile.objects.all()
    serializer_class = serializers.ProfileSerializer


class OnPremiseWorkplaceViewSet(viewsets.ModelViewSet):
    queryset = models.OnPremiseWorkplace.objects.all()
    serializer_class = serializers.OnPremiseWorkplaceSerializer
    permission_classes = [customPermissions.OnPremiseWorkplacePermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        logger.info(self.request.GET)
        if 'displayed' in self.request.GET:
            if self.request.GET['displayed'] in ['True', 'true']:
                queryset = queryset.filter(displayed=True)

        return queryset

    @action(detail=True, url_path="slots", methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def get_slots(self, request: Request, pk=None):
        """
        return all Timeslots which are bookable [{start: time, end:time, weekday: int, date:date ,disabled: bool}]
        """
        weekdays = models.Settings.objects.get(
            type='onpremise_weekdays').value.replace(' ', '').split(',')
        temp = models.Settings.objects.get(
            type='onpremise_starttime').value.replace(' ', '').split(':')
        onpremise_start_hour = int(temp[0])
        onpremise_start_min = int(temp[1] if len(temp) > 1 else 0)
        temp = models.Settings.objects.get(
            type='onpremise_endtime').value.replace(' ', '').split(':')
        onpremise_end_hour = int(temp[0])
        onpremise_end_min = int(temp[1] if len(temp) > 1 else 0)
        onpremise_break = timedelta(minutes=int(models.Settings.objects.get(
            type='onpremise_breakinbetween_in_min').value.replace(' ', '')))
        onpremise_date_range = int(models.Settings.objects.get(
            type='onpremise_date_range_in_days').value.replace(' ', ''))
        duration = timedelta(minutes=int(models.Settings.objects.get(
            type='onepremise_slotduration').value.replace(' ', '')))
        ret = []
        excluded_workplaces = models.OnPremiseWorkplace.objects.get(
            pk=pk).exclusions.all()
        for diff in range(onpremise_date_range):
            delta = timedelta(days=diff)
            now = timezone.now().astimezone(tz=timezone.get_default_timezone())
            slot_day = now + delta
            if str(slot_day.isoweekday()) not in weekdays:
                continue

            init_start_hour = onpremise_start_hour
            init_start_min = onpremise_start_min
            start = slot_day.replace(
                hour=init_start_hour, minute=init_start_min, second=0, microsecond=0)
            while (start + duration <= slot_day.replace(hour=onpremise_end_hour, minute=onpremise_end_min, second=0, microsecond=0)):
                slot_start = start
                slot_end = start + duration
                # fetch all bookings in the slot that are not canceled
                bookings = models.OnPremiseBooking.objects.filter(
                    slot_start__lte=slot_end, slot_end__gte=slot_start, workplace_id=pk, canceled__isnull=True)
                # general disabled time
                blocked = models.OnPremiseBlockedTimes.objects.filter(
                    starttime__lte=slot_end, endtime__gte=slot_start)
                # fetch status
                status = models.OnPremiseWorkplaceStatus.objects.filter(
                    from_date__lte=slot_end, until_date__gte=slot_start, workplace_id=pk)
                exclusion_bookings = models.OnPremiseBooking.objects.filter(
                    workplace__in=excluded_workplaces, slot_start__lte=slot_end, slot_end__gte=slot_start)
                ret.append({'start': slot_start, 'end': slot_end, 'weekday': slot_day.weekday(), 'date': start.date(
                ), 'disabled': (bookings.count() != 0 or status.count() != 0 or blocked.count() != 0 or exclusion_bookings.count() != 0)})
                start = slot_end + onpremise_break

        return Response(ret)


class OnPremiseBookingViewSet(viewsets.ModelViewSet):
    queryset = models.OnPremiseBooking.objects.all()
    serializer_class = serializers.OnPremiseBookingSerializer
    permission_classes = [customPermissions.OnPremiseBookingPermission]

    @action(detail=True, url_path="cancel", methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def cancel_onpremise_booking(self, request: Request, pk=None):
        booking = models.OnPremiseBooking.objects.get(pk=pk)
        booking.canceled = timezone.now()
        booking.save()
        serializer = serializers.OnPremiseBookingSerializer(booking,context={'request': request})
        return Response(serializer.data)

    def get_queryset(self):
        queryset = self.queryset
        querydict = self.request.GET
        if 'self' in querydict:
            if querydict['self'] in ['True', 'true']:
                queryset = queryset.filter(user=self.request.user)
        if 'from_date' in querydict:
            queryset = queryset.filter(slot_start__date__gte=datetime.strptime(
                querydict['from_date'], '%Y-%m-%d').date())
        if 'until_date' in querydict:
            queryset = queryset.filter(slot_start__date__lte=datetime.strptime(
                querydict['until_date'], '%Y-%m-%d').date())
        if 'canceled' in querydict:
            if querydict['canceled'] in ['False', 'false']:
                queryset = queryset.filter(canceled__isnull=True)
        return queryset


class OnPremiseBlockedTimesViewSet(viewsets.ModelViewSet):
    queryset = models.OnPremiseBlockedTimes.objects.all()
    serializer_class = serializers.OnPremiseBlockedTimesSerializer
    permission_classes = [customPermissions.OnPremiseBlockedTimesPermission]
