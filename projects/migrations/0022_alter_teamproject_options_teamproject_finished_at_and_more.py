# Generated by Django 5.0 on 2025-06-27 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0021_alter_submission_team_teamproject_delete_userproject'),
        ('teams', '0012_team_uuid'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='teamproject',
            options={'ordering': ['-created_at'], 'verbose_name': 'Team Project', 'verbose_name_plural': 'Team Projects'},
        ),
        migrations.AddField(
            model_name='teamproject',
            name='finished_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name='teamproject',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('finished_at__isnull', False), ('is_finished', True)), models.Q(('finished_at__isnull', True), ('is_finished', False)), _connector='OR'), name='finished_at_check'),
        ),
        migrations.AddConstraint(
            model_name='teamproject',
            constraint=models.UniqueConstraint(fields=('team', 'project'), name='unique_team_project'),
        ),
    ]
