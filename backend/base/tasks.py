from celery import shared_task
from django.forms import model_to_dict
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.db import transaction
from django.template import Context, Template

from django_celery_beat.models import PeriodicTask

from datetime import timedelta, datetime

from base import models
import logging

logger = logging.getLogger("django")


@shared_task()
def task_execute():
    rentals = models.Rental.objects.all()
    ret = []
    for rental in rentals:
        logger.info(rental.handed_out_at)
        ret.append(model_to_dict(rental))
    return ret


@shared_task()
def cleanup_accounts():
    """
    Delete all accounts where the email has not been verified
    """
    users = User.objects.filter(last_login__isnull=True, date_joined__lte=timezone.now(
    ) - timedelta(weeks=2), is_active=False)
    result, _ = users.delete()
    # 23 need to divide it by 2 because profiles also count against the count
    return f"deleted {result/2} accounts"


@shared_task()
def notify_about_rentals_and_reservations():
    """
    fetch all reservations for the next day 
    """
    reservations = models.Reservation.objects.filter(reserved_from__lte=(timezone.now(
    ) + timedelta(days=1)).date(), reserved_from__gte=timezone.now().date(), canceled__isnull=True, notified__isnull=True)
    count_mails = 0
    if len(reservations) > 0:
        with transaction.atomic():
            template_data = {"reservations": []}
            for reservation in reservations:
                reservation_dict = model_to_dict(reservation)
                reservation_dict['reserver_profile'] = model_to_dict(
                    reservation.reserver)
                reservation_dict['reserver_user'] = model_to_dict(
                    reservation.reserver.user)
                reservation_dict['objecttype'] = model_to_dict(
                    reservation.objecttype)
                template_data['reservations'].append(reservation_dict)
            logger.info(template_data)
            # notify lender about reservations one day in advance
            template = Template(models.Text.objects.filter(
                name='reservation_lender_notification').first().content)
            message = template.render(Context(template_data))
            count_mails = send_mail(subject="Neue Reservierungen am " + str(template_data["reservations"][0]['reserved_from']),
                                    from_email=settings.DEFAULT_FROM_EMAIL, message=message, html_message=message, recipient_list=[settings.DEFAULT_NOTIFICATION_EMAIL])
            reservations.update(notified=timezone.now())

    rentals = [ r for r in models.Rental.objects.filter( received_back_at__isnull=True, notified__isnull=True) if r.extended_until==(
        timezone.now() + timedelta(days=2)).date()]
    count_rental_mails = 0
    if len(rentals) > 0:
        with transaction.atomic():
            template_data = {}
            for rental in rentals:
                rental_dict = model_to_dict(rental)
                if rental.reservation.reserver.user.pk not in template_data:
                    user = rental.reservation.reserver.user
                    template_data[user.pk] = {'user': model_to_dict(user), 'rentals': [], 'return_date_info': {'date': rental.extended_until(), 'start': models.Settings.objects.get(
                        type='returning_start_hour').value, 'end': models.Settings.objects.get(type='returning_end_hour').value}}
                rental_dict['rented_object'] = model_to_dict(
                    rental.rented_object)
                rental_dict['rented_object']['type'] = model_to_dict(
                    rental.rented_object.type)
                rental_dict['rented_object']['merged_identifier'] = rental.rented_object.type.prefix_identifier + \
                    str(rental.rented_object.internal_identifier)
                template_data[user.pk]['rentals'].append(rental_dict)
            for key in template_data.keys():
                template = Template(models.Text.objects.filter(
                    name='rental_expiration_notification').first().content)
                message = template.render(Context(template_data[key]))
                count_rental_mails += send_mail(subject=f"Deine ausgeliehenen Gegenstände müssen am {template_data[key]['return_date_info']['date']} zurück",
                                                from_email=settings.DEFAULT_FROM_EMAIL, message=message, html_message=message, recipient_list=[template_data[key]['user']['email']])
                logger.info(message)
            rentals.update(notified=timezone.now())
    # only execute if returning hours are over
    if timezone.now() > timezone.now().replace(hour=int(models.Settings.objects.get(type='returning_end_hour').value), minute=0, second=0):
        # reuse notified state for this fetch all rentals that were supposed to come back today and which have been notified about reserved until before the rental hour startet
        rentals_not_received_back = [ r for r in models.Rental.objects.filter(received_back_at__isnull=True, notified__lte=timezone.now(
            ).replace(hour=int(models.Settings.objects.get(type='returning_start_hour').value))) if r.extended_until==timezone.now().date()]
        if len(rentals_not_received_back) > 0:
            message="Wir haben ein paar Gegenstände nicht zurückerhalten, bitte einmal überprüfen."
            send_mail(subject=f"Fehlende Gegenstände für heutige Rückgabe",
                from_email=settings.DEFAULT_FROM_EMAIL, message=message, html_message=message, recipient_list=[settings.DEFAULT_NOTIFICATION_EMAIL])
            rentals.update(notified=timezone.now())
    return f"send {count_mails} mails about reservations"
