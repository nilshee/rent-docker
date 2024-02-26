# Generated by Django 4.1.4 on 2023-01-07 14:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0028_alter_rentalobjectstatus_from_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rentalobjectstatus',
            name='rentable',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='rentalobjectstatus',
            name='rental_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.rentalobject', verbose_name='Rentalobject'),
        ),
    ]