# Generated by Django 5.0 on 2025-06-27 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0009_invitation_is_active_invitation_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
