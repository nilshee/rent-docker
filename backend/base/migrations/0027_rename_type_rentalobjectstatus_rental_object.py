# Generated by Django 4.1.4 on 2023-01-06 20:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0026_alter_profile_user_rentalobjectstatus'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rentalobjectstatus',
            old_name='type',
            new_name='rental_object',
        ),
    ]