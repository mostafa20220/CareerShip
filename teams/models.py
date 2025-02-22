from celery.utils.deprecated import Property
from django.db import models
from django.urls import reverse
import  datetime as dt
from django.utils import timezone
from users.models import User

class Team(models.Model):
    name = models.CharField(max_length=255)
    is_private = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)

class TeamProject(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, db_index=True, related_name='team_projects')
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, db_index=True, related_name='team_projects')

class TeamUser(models.Model):
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, db_index=True, related_name='teams')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, db_index=True, related_name='team_users')


class Invitation(models.Model):
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, db_index=True, related_name='invitations')
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='invitations')
    created_at = models.DateTimeField(auto_now_add=True ,db_index=True)
    expires_in_days = models.PositiveSmallIntegerField(default=3)



    def is_expired(self):
         expiration_date = self.created_at + dt.timedelta(days=self.expires_in_days)
         return timezone.now() > expiration_date

    def __str__(self):
        return f"Invitation created at {self.created_at}, expires in {self.expires_in_days} days"

    def get_invitation_url(self):
        return reverse('invitation_detail', kwargs={'pk': self.pk})




