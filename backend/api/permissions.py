from rest_framework import permissions
from rest_framework.request import Request

from django.http import HttpRequest

from api import views
from base import models

import logging
logger = logging.getLogger('django')

class UserPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        logger.info('lol1')
        logger.info(request.user.is_authenticated)
        logger.info(request.user.is_superuser)
        logger.info(view.action)
        if view.action in ['list', 'toggle_permission']:
            return request.user.is_authenticated and request.user.is_superuser
        elif view.action == 'create':
            return True
        elif view.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return True
        else:
            return False

    def has_object_permission(self, request:HttpRequest, view, obj):
        # Deny actions on objects if the user is not authenticated
        logger.info('lol2')
        if not request.user.is_authenticated:
            return False
        logger.info(request.user.is_superuser)
        if view.action == 'retrieve':
            return obj == request.user or request.user.is_superuser
        elif view.action in ['destroy', 'update', 'partial_update', 'list']:
            return request.user.is_superuser
        else:
            return False

class GroupPermission(permissions.BasePermission):
    def has_permission(self, request:HttpRequest, view):
        if view.action == 'list':
            return request.user.is_authenticated and request.user.is_superuser
        elif view.action == 'create':
            return request.user.is_authenticated and request.user.is_superuser
        elif view.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return True
        else:
            return False

    def has_object_permission(self, request:HttpRequest, view, obj):
        # Deny actions on objects if the user is not authenticated
        if not request.user.is_authenticated:
            return False

        if view.action == 'retrieve':
            return request.user.is_superuser
        elif view.action in ['destroy', 'update', 'partial_update', 'list']:
            return request.user.is_superuser
        else:
            return False

class RentalObjectTypePermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        Non staff users shouldn't be able to change Rentalobjecttypes 
        """
        if view.action in ['retrieve', 'list']:
            return True
        elif view.action in ['destroy', 'update', 'partial_update', 'create']:
            return request.user.has_perm('base.inventory_editing')
        elif view.action == 'currently_free_objects':
            return request.user.has_perm('base.lending_access')
        return False

    def has_object_permission(self, request:Request, view, obj:models.RentalObjectType):
        if not request.user.has_perm('base.lending_access') and obj.visible == False:
            return False
        return super().has_object_permission(request, view, obj)

class RentalObjectPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        Non staff users shouldn't be able to change Rentalobject 
        """
        if not request.user.is_authenticated:
            return False
            
        if view.action in ['retrieve']:
            return True
        elif view.action in ['list']:
            return request.user.is_staff
        elif view.action in ['destroy', 'update', 'partial_update', 'create']:
            return request.user.has_perm('base.inventory_editing')
        return False
        
    def has_object_permission(self, request:Request, view, obj:models.RentalObject):
        if not request.user.is_staff and obj.rentable == False:
            return False
        return super().has_object_permission(request, view, obj)


class CategoryPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        Non staff users shouldn't be able to change Categories 
        """
        if view.action in ['retrieve','list']:
            return True
        elif view.action in ['destroy', 'update', 'partial_update', 'create']:
            return request.user.has_perm('base.inventory_editing')
        return False

class ReservationPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        Users should be able to cancel own reservations but shouldnt be able to edit those 
        """
        if not request.user.is_authenticated:
            return False
        print(view.action)
        if view.action in ['retrieve', 'bulk_create', 'cancel_reservation', 'list']:
            return True
        elif view.action in ['list', 'create', 'download_form', 'currently_selected_objects']:
            return request.user.has_perm('base.lending_access')
        elif view.action in ['destroy', 'update', 'partial_update']:
            return request.user.has_perm('base.inventory_editing')
        return False
        
    def has_object_permission(self, request:Request, view, obj:models.Reservation):
        if view.action in ['cancel_reservation','retrieve', 'list']:
            return obj.reserver == request.user or request.user.has_perm('base.lending_access')

        return True
        

class RentalPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        Users should be able to extend own rentals 
        """
        if not request.user.is_authenticated:
            return False
            
        if view.action in ['retrieve', 'cancel_reservation','list']:
            return True
        elif view.action in ['bulk_rental_creation', 'bulk_return', 'download_form', 'create']:
            return request.user.has_perm('base.lending_access')
        elif view.action in ['destroy', 'update', 'partial_update']:
            return request.user.has_perm('base.inventory_editing')
        return False
        
    def has_object_permission(self, request:Request, view, obj:models.Rental):
        if view.action in ['extend_rental','retrieve', 'list']:
            return obj.reservation.reserver == request.user or request.user.has_perm('base.lending_access')

        return True

class TextPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        Users should be able to see public texts 
        """
            
        if view.action in ['retrieve','list']:
            return True
        elif view.action in []:
            return request.user.has_perm('base.lending_access')
        elif view.action in ['destroy', 'update', 'partial_update', 'create']:
            return request.user.has_perm('base.inventory_editing')
        return False

class TagPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        Users should be able to see public tags
        """
        if view.action in ['retrieve','list']:
            return True
        elif view.action in []:
            return request.user.has_perm('base.lending_access')
        elif view.action in ['destroy', 'update', 'partial_update', 'create']:
            return request.user.has_perm('base.inventory_editing')
        return False

class PriorityPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        The user does not need to edit the prio directly
        """
        if view.action in []:
            return True
        elif view.action in []:
            return request.user.has_perm('base.lending_access')
        elif view.action in ['retrieve','list','destroy', 'update', 'partial_update', 'create']:
            return request.user.has_perm('base.inventory_editing')
        return False

class SettingsPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        The user should only see public permission
        """
        if view.action in ['retrieve','list',]:
            return True
        elif view.action in []:
            return request.user.has_perm('base.lending_access')
        elif view.action in ['destroy', 'update', 'partial_update', 'create']:
            return request.user.has_perm('base.inventory_editing')
        return False
        
    def has_object_permission(self, request:Request, view, obj:models.Settings):
        if not request.user.has_perm('base.inventory_editing') and not obj.public:
            return False
        return True

class MaxRentDurationPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        if view.action in ['retrieve','list',]:
            return True
        elif view.action in []:
            return request.user.has_perm('base.lending_access')
        elif view.action in ['destroy', 'update', 'partial_update', 'create']:
            return request.user.has_perm('base.inventory_editing')
        return False

class FilesPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        Filling the form in is handled in another view so we do not need to allow basic CRUD here
        """
        if view.action in []:
            return True
        elif view.action in []:
            return request.user.has_perm('base.lending_access')
        elif view.action in ['retrieve','list','destroy', 'update', 'partial_update', 'update_rental_form_set', 'download', 'create']:
            return request.user.has_perm('base.inventory_editing')
        return False

class OnPremiseWorkplacePermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        The user should be able to the workplaces
        """
        if view.action in ['retrieve','list', 'get_slots']:
            return True
        elif view.action in []:
            return request.user.has_perm('base.lending_access')
        elif view.action in ['destroy', 'update', 'partial_update', 'create']:
            return request.user.has_perm('base.inventory_editing')
        return False

class OnPremiseBookingPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        The user should only see public permission
        """
        if view.action in ['retrieve','list', 'cancel_onpremise_booking', 'create']:
            return True
        elif view.action in []:
            return request.user.has_perm('base.lending_access')
        elif view.action in ['destroy', 'update', 'partial_update']:
            return request.user.has_perm('base.inventory_editing')
        return False
        
    def has_object_permission(self, request:Request, view, obj:models.OnPremiseBooking):
        if not request.user.has_perm('base.lending_access') and obj.user != request.user:
            return False
        return True

        

class OnPremiseBlockedTimesPermission(permissions.BasePermission):
    def has_permission(self, request:Request, view):
        """
        Available solts are generated in backend. therefore a normal user does not need direct access
        """
        if view.action in []:
            return True
        elif view.action in []:
            return request.user.has_perm('base.lending_access')
        elif view.action in ['retrieve','list', 'destroy', 'update', 'partial_update', 'create']:
            return request.user.has_perm('base.inventory_editing')
        return False