# Generated by Django 4.1.4 on 2023-01-02 20:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0020_text_slug'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='text',
            name='slug',
        ),
    ]