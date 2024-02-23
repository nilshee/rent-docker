from django.contrib import admin
from django.contrib.auth.models import Permission

from . import models


# Register your models here.
admin.site.register(models.RentalObject)
admin.site.register(models.RentalObjectType)
admin.site.register(models.Category)
admin.site.register(models.Priority)
admin.site.register(models.Profile)
admin.site.register(Permission)
admin.site.register(models.Reservation)
admin.site.register(models.Rental)
admin.site.register(models.Tag)
admin.site.register(models.Text)
admin.site.register(models.RentalObjectStatus)
admin.site.register(models.Settings)
admin.site.register(models.MaxRentDuration)
admin.site.register(models.Files)
admin.site.register(models.OauthVerificationProcess)
admin.site.register(models.Suggestion)
admin.site.register(models.OnPremiseBlockedTimes)
admin.site.register(models.OnPremiseBooking)
admin.site.register(models.OnPremiseWorkplace)
admin.site.register(models.OnPremiseWorkplaceStatus)
admin.site.register(models.PasswordReset)
admin.site.register(models.Extension)