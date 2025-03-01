from django.db import models


class Prerequisite(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    def __str__(self ):
        return self.name


class TaskPrerequisite(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, db_index=True)
    prerequisite = models.ForeignKey(
        'Prerequisite', on_delete=models.CASCADE, db_index=True,related_name='tasks'
    )
