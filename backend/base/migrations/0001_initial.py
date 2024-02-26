# Generated by Django 4.1.1 on 2022-10-10 12:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(default='email', max_length=100)),
                ('receiver', models.CharField(max_length=255)),
                ('subject', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('sent_at', models.DateTimeField(null=True)),
                ('send_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='OnPremiseBlockedTimes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('starttime', models.DateTimeField(default=None)),
                ('endtime', models.DateTimeField(default=None)),
            ],
        ),
        migrations.CreateModel(
            name='OnPremiseTimeSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.SmallIntegerField()),
                ('start_time', models.TimeField()),
                ('duration', models.DurationField()),
            ],
        ),
        migrations.CreateModel(
            name='Priority',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prio', models.PositiveSmallIntegerField(verbose_name='priority in renting queue')),
                ('name', models.CharField(max_length=100, verbose_name='name of the priority class')),
                ('description', models.CharField(max_length=255, null=True, verbose_name='description of the priority class')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('authorized', models.BooleanField(verbose_name='authorized to rent objects')),
                ('newsletter', models.BooleanField(verbose_name='newsletter signup')),
                ('prio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.priority')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RentalObject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_identifier', models.CharField(max_length=20)),
                ('inventory_number', models.CharField(max_length=100, null=True)),
                ('rentable', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='RentalObjectType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(default='')),
                ('visible', models.BooleanField(default=False)),
                ('image', models.ImageField(upload_to='')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.category')),
            ],
        ),
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=100)),
                ('value', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Suggestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('suggestion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suggestion', to='base.rentalobjecttype')),
                ('suggestion_for', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suggestion_for', to='base.rentalobjecttype')),
            ],
        ),
        migrations.CreateModel(
            name='RentalOperation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rejected', models.BooleanField()),
                ('operation_number', models.BigIntegerField()),
                ('reserved_at', models.DateTimeField(auto_now_add=True)),
                ('reserved_from', models.DateTimeField()),
                ('reserved_until', models.DateTimeField()),
                ('picked_up_at', models.DateTimeField(default=None, null=True)),
                ('handed_out_at', models.DateTimeField(default=None, null=True)),
                ('received_back_at', models.DateTimeField(default=None, null=True)),
                ('lender', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lender', to=settings.AUTH_USER_MODEL)),
                ('object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.rentalobject')),
                ('renter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='renter', to='base.profile')),
            ],
        ),
        migrations.AddField(
            model_name='rentalobject',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.rentalobjecttype'),
        ),
        migrations.CreateModel(
            name='PublicInfoObjectType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=20, verbose_name='bootstrap type')),
                ('content', models.TextField()),
                ('objecttype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.rentalobjecttype')),
            ],
        ),
        migrations.CreateModel(
            name='OnPremiseBooking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('showed_up', models.BooleanField()),
                ('start_datetime', models.DateTimeField()),
                ('duration', models.DurationField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='InternalInfoObjectType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=20, verbose_name='bootstrap type')),
                ('content', models.TextField()),
                ('objecttype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.rentalobjecttype')),
            ],
        ),
    ]