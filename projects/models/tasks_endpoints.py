from django.contrib.postgres.fields import ArrayField
from django.db import models


class Task(models.Model):
    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE, db_index=True, related_name="tasks"
    )
    difficulty_level = models.ForeignKey(
        'DifficultyLevel',
        on_delete=models.SET_NULL,
        db_index=True,
        related_name='tasks',
        null=True,
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    duration_in_days = models.PositiveSmallIntegerField(default=1)
    tests = ArrayField(models.TextField(), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self ):
        return self.name



GET = 'GET'
POST = 'POST'
PUT = 'PUT'
PATCH = 'PATCH'
DELETE = 'DELETE'
method_choices=(
    (GET, 'GET'),
    (POST, 'POST'),
    (PUT, 'PUT'),
    (PATCH, 'PATCH'),
    (DELETE, 'DELETE'),
)


class Endpoint(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, db_index=True)
    method = models.CharField(choices=method_choices,max_length=10)
    path = models.TextField()
    description = models.TextField(blank=True, null=True)

    def __str__(self ):
        return self.method + " - " +  self.path
