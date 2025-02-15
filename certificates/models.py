from django.db import models

# Create your models here.

class Certificate(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, db_index=True)
    no = models.UUIDField(unique=True)
    created_at = models.DateField(auto_now_add=True)
