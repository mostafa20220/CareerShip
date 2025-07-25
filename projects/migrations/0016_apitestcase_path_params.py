# Generated by Django 5.0 on 2025-06-23 03:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0015_alter_testcase_options_testcase_order_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='apitestcase',
            name='path_params',
            field=models.JSONField(blank=True, help_text="Parameters to substitute into the endpoint path, e.g., {'id': 99999} or {'id': '{{context.id}}'}", null=True),
        ),
    ]
