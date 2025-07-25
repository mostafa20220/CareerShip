from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField


STUDENT = 'student'
ADMIN = 'admin'

USER_TYPE_CHOICES = (
    (STUDENT, 'Student'),
    (ADMIN, 'Admin')
)

class CustomUserManager(BaseUserManager):

    def create(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email=email)



class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    user_type = models.CharField(choices=USER_TYPE_CHOICES, default=STUDENT, max_length=50)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    phone =  PhoneNumberField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    google_id = models.CharField(max_length=255, blank=True, null=True)
    github_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def is_student(self):
        return self.user_type == STUDENT

    def is_admin(self):
        return self.user_type == ADMIN

    def __str__(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email


@receiver(post_save, sender=User)
def create_user_team(sender, instance, created, **kwargs):
    if created:
        from teams.models import Team
        team_name = f"{instance.first_name}'s Team" if instance.first_name else f"Team {instance.pk}"
        Team.create_with_owner(name=team_name, owner=instance)


class Skill(models.Model):
    name = models.CharField(max_length=255, unique=True)


class UserSkills(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, db_index=True)
    skill = models.ForeignKey('Skill', on_delete=models.CASCADE, db_index=True)

    class Meta:
        unique_together = ('user', 'skill')
