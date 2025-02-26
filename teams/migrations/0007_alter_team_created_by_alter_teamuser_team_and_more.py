# Generated by Django 5.0 on 2025-02-26 15:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0006_alter_teamuser_team'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_teams', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='teamuser',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_users', to='teams.team'),
        ),
        migrations.AlterField(
            model_name='teamuser',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_memberships', to=settings.AUTH_USER_MODEL),
        ),
    ]
