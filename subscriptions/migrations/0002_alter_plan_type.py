# Generated by Django 5.0 on 2025-02-15 20:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plan',
            name='type',
            field=models.CharField(choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')], max_length=50),
        ),
    ]
