# Generated by Django 5.0 on 2025-02-25 18:18

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_remove_task_duration_task_description_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='is_pass',
        ),
        migrations.AddField(
            model_name='submission',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='execution_logs',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='failed_test_index',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='submission',
            name='passed_percentage',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='submission',
            name='passed_tests',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='submission',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('passed', 'Passed'), ('failed', 'Failed')], default='pending', max_length=50),
        ),
        migrations.AddField(
            model_name='task',
            name='tests',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), blank=True, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='endpoint',
            name='method',
            field=models.CharField(choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('PATCH', 'PATCH'), ('DELETE', 'DELETE')], max_length=10),
        ),
        migrations.AlterField(
            model_name='submission',
            name='feedback',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
