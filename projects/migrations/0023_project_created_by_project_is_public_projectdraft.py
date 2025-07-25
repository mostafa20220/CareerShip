# Generated by Django 5.0 on 2025-07-03 23:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0022_alter_teamproject_options_teamproject_finished_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_projects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='project',
            name='is_public',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.CreateModel(
            name='ProjectDraft',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_public', models.BooleanField(default=False)),
                ('conversation_history', models.JSONField(blank=True, default=list)),
                ('latest_project_json', models.JSONField(blank=True, default=dict)),
                ('status', models.CharField(choices=[('generating', 'Generating'), ('pending_review', 'Pending Review'), ('completed', 'Completed'), ('archived', 'Archived')], default='generating', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.category')),
                ('difficulty_level', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='projects.difficultylevel')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
