# Generated by Django 5.0 on 2025-02-22 21:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_remove_task_duration_task_description_and_more'),
        ('teams', '0004_alter_team_created_by'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitation',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='teamproject',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_projects', to='projects.project'),
        ),
        migrations.AlterField(
            model_name='teamproject',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_projects', to='teams.team'),
        ),
        migrations.AlterField(
            model_name='teamuser',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='users', to='teams.team'),
        ),
        migrations.AlterField(
            model_name='teamuser',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_users', to=settings.AUTH_USER_MODEL),
        ),
    ]
