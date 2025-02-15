from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    user_type = models.CharField(max_length=255)
    avatar = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    google_id = models.CharField(max_length=255, blank=True, null=True)
    github_id = models.CharField(max_length=255, blank=True, null=True)

class Skill(models.Model):
    name = models.CharField(max_length=255, unique=True)

class UserSkills(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, db_index=True)
    skill = models.ForeignKey('Skill', on_delete=models.CASCADE, db_index=True)
