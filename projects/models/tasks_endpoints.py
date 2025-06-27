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
    order = models.PositiveIntegerField(
        default=0,
        help_text="Execution order of the task within a project (0, 1, 2...).")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['project', 'order'] # Default ordering
        constraints = [
            models.UniqueConstraint(fields=['project', 'order'], name='unique_task_order_per_project')
        ]

    def __str__(self ):
        return self.name


class MethodType(models.TextChoices):
    GET = 'GET', 'GET'
    POST = 'POST', 'POST'
    PUT = 'PUT', 'PUT'
    PATCH = 'PATCH', 'PATCH'
    DELETE = 'DELETE', 'DELETE'

class Endpoint(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, db_index=True)
    method = models.CharField(choices=MethodType.choices,max_length=10)
    path = models.TextField()
    description = models.TextField(blank=True, null=True)

    def __str__(self ):
        return self.method + " - " +  self.path