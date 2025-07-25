# Generated by Django 5.0 on 2025-06-24 23:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0017_alter_task_options_task_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='task',
            options={'ordering': ['project', 'order']},
        ),
        migrations.AlterField(
            model_name='task',
            name='order',
            field=models.PositiveIntegerField(default=0, help_text='Execution order of the task within a project (0, 1, 2...).'),
        ),
        migrations.AddConstraint(
            model_name='task',
            constraint=models.UniqueConstraint(fields=('project', 'order'), name='unique_order_per_project'),
        ),
    ]
