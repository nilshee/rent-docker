from django.apps import AppConfig
from django.db.models.signals import post_migrate


class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'

    def ready(self) -> None:
        """
        create every setting from settings.py that is supposed to exist in db in the db. we need to do those ugly imports here because models are not initialized otherwise
        """
        from django_celery_beat.models import PeriodicTask
        from django_celery_beat.models import IntervalSchedule
        from .signals import populate_models
        import logging
        from base import models
        from django.conf import settings
        # deprecated
        #post_migrate.connect(populate_models, sender=self)
        logger = logging.getLogger("django")
        if not models.Settings.objects.filter(type='lenting_day').exists():
            logger.info(f"creating lenting_day with {settings.DEFAULT_LENTING_DAY_OF_WEEK} in db")
            models.Settings.objects.create(
                type='lenting_day', value=settings.DEFAULT_LENTING_DAY_OF_WEEK, public=True)

        if not models.Settings.objects.filter(type='lenting_start_hour').exists():
            logger.info(f"creating lenting_start_hour with {settings.DEFAULT_LENTING_START_HOUR} in db")
            models.Settings.objects.create(
                type='lenting_start_hour', value=settings.DEFAULT_LENTING_START_HOUR, public=True)

        if not models.Settings.objects.filter(type='lenting_end_hour').exists():
            logger.info(f"creating lenting_end_hour with {settings.DEFAULT_LENTING_END_HOUR} in db")
            models.Settings.objects.create(
                type='lenting_end_hour', value=settings.DEFAULT_LENTING_END_HOUR, public=True)

        if not models.Settings.objects.filter(type='returning_day').exists():
            logger.info(f"creating returning_day with {settings.DEFAULT_RETURNING_DAY_OF_WEEK} in db")
            models.Settings.objects.create(
                type='returning_day', value=settings.DEFAULT_RETURNING_DAY_OF_WEEK, public=True)

        if not models.Settings.objects.filter(type='returning_start_hour').exists():
            logger.info(f"creating returning_start_hour with {settings.DEFAULT_RETURNING_START_HOUR} in db")
            models.Settings.objects.create(
                type='returning_start_hour', value=settings.DEFAULT_RETURNING_START_HOUR, public=True)

        if not models.Settings.objects.filter(type='returning_end_hour').exists():
            logger.info(f"creating returning_end_hour with {settings.DEFAULT_RETURNING_END_HOUR} in db")
            models.Settings.objects.create(
                type='returning_end_hour', value=settings.DEFAULT_RETURNING_END_HOUR, public=True)

        if not models.Settings.objects.filter(type='email_validation_regex').exists():
            logger.info(f"creating email_validation_regex with {settings.EMAIL_VALIDATION_REGEX} in db")
            models.Settings.objects.create(type='email_validation_regex', value=settings.EMAIL_VALIDATION_REGEX, public=True)

        if not models.Settings.objects.filter(type='onepremise_slotduration').exists():
            logger.info(f"creating onepremise_slotduration with {90} in db")
            models.Settings.objects.create(type='onepremise_slotduration', value='90', public=True)

        if not models.Settings.objects.filter(type='onpremise_date_range_in_days').exists():
            logger.info(f"creating onpremise_date_range_in_days with {7} in db")
            models.Settings.objects.create(type='onpremise_date_range_in_days', value='7', public=True)
        

        if not models.Settings.objects.filter(type='onpremise_weekdays').exists():
            logger.info(f"creating onpremise_weekdays with {'1,2,3,4,5'} in db")
            models.Settings.objects.create(type='onpremise_weekdays', value='1,2,3,4,5', public=True)

        if not models.Settings.objects.filter(type='onpremise_date_range_in_days').exists():
            logger.info(f"creating onpremise_date_range_in_days with {7} in db")
            models.Settings.objects.create(type='onpremise_date_range_in_days', value='7', public=True)

        if not models.Settings.objects.filter(type='onpremise_activated').exists():
            logger.info(f"creating onpremise_activated with {True} in db")
            models.Settings.objects.create(type='onpremise_activated', value='True', public=True)

        if not models.Settings.objects.filter(type='onpremise_breakinbetween_in_min').exists():
            logger.info(f"creating onpremise_breakinbetween_in_min with {30} in db")
            models.Settings.objects.create(type='onpremise_breakinbetween_in_min', value='30', public=True)

        if not models.Settings.objects.filter(type='onpremise_endtime').exists():
            logger.info(f"creating onpremise_endtime with {18} in db")
            models.Settings.objects.create(type='onpremise_endtime', value='18', public=True)

        if not models.Settings.objects.filter(type='onpremise_starttime').exists():
            logger.info(f"creating onpremise_starttime with {'10:30'} in db")
            models.Settings.objects.create(type='onpremise_starttime', value='10:30', public=True)

        """
        populate some defaults, for example the default priority class, or default texts
        """
        if not models.Priority.objects.filter(prio=99).exists():
            logger.info(f"creating unverified priority in db")
            models.Priority.objects.create(
                prio=99, name="unverified", description="Default renting class, should be the one with the shortest renting durations")

        if not models.Priority.objects.filter(prio=50, name="automatically verified").exists():
            logger.info(f"creating auto verified Priority in db")
            models.Priority.objects.create(
                prio=50, name="automatically verified", description="Person is automatically verified.")

        if not models.Priority.objects.filter(prio=49).exists():
            logger.info(f"creating manually verified Prio in db")
            models.Priority.objects.create(
                prio=49, name="manually verified", description="Person is manually verified.")

        if not models.Text.objects.filter(name='signup_mail').exists():
            logger.info(f"creating default signup_mail in db")
            models.Text.objects.create(
                name='signup_mail', content=r"Hallo {{first_name}}, bitte aktiviere dein Konto unter {{validation_link}}")
    
        if not PeriodicTask.objects.filter(task="base.tasks.notify_about_rentals_and_reservations").exists():
            logger.info(f"creating lenting_day with {settings.DEFAULT_LENTING_DAY_OF_WEEK} in db")
            PeriodicTask.objects.create(name="Send Notifications about rentals and reservations", task="base.tasks.notify_about_rentals_and_reservations", args=[], kwargs={}, enabled=True, interval_id=IntervalSchedule.objects.get_or_create(every=30, period="minutes")[0].pk)

        if not PeriodicTask.objects.filter(task="base.tasks.cleanup_accounts").exists():
            logger.info(f"creating lenting_day with {settings.DEFAULT_LENTING_DAY_OF_WEEK} in db")
            PeriodicTask.objects.create(name="Delete created, but never activated accounts", task="base.tasks.cleanup_accounts", args=[], kwargs={}, enabled=True, interval_id=IntervalSchedule.objects.get_or_create(every=1, period="days")[0].pk)