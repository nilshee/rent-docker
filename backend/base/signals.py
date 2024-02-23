from django.contrib.auth.models import User, Group, Permission
from base.models import Priority
import logging

logger = logging.getLogger("django")


def populate_models(sender, **kwargs):
    pass
    #TODO rework setup maybe on creation?
    # # create groups
    # try:
    #     # test if a user exists, if not create a adminuser asuming the first user would be the admin user. 
    #     # If the user exists assume that the creation of the default objects already happenend
    #     User.objects.get(id=1)
    #     Group.objects.get(name='employee')
    #     Group.objects.get(name='lender')
    # except:
    #     new_User = User.objects.create_user(
    #         username='admin', is_staff=True, is_superuser=True, password='admin')
    #     # employees are a group with general access. but not neccessary editing rights
    #     employee_group, created = Group.objects.get_or_create(
    #         name='employees')
    #     # lenders a group with lending rights, therefore are able to lend objects to people
    #     lender_group, created = Group.objects.get_or_create(name='lenders')
    #     admin_group, creater = Group.objects.get_or_create(name='admins')
        
    #     # assign permissions to groups
    #     general_access_permission = Permission.objects.get(codename='general_access')
    #     lending_access_permission = Permission.objects.get(codename='lending_access')
    #     inventory_editing_permission = Permission.objects.get(codename='inventory_editing')
    #     employee_group.permissions.add(general_access_permission)
    #     lender_group.permissions.add(lending_access_permission)
    #     admin_group.permissions.add(inventory_editing_permission)
    # try:
    #     Priority.objects.get(prio=99)
    # except:
    #     Priority.objects.create(name='Default', prio=99, description='default class')