from django.db import models
from django.conf import settings
from django.urls import reverse
import datetime as dt
from django.utils import timezone

class Team(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_teams')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def add_member(self, user):
        """Add a new member to the team."""
        self.members.add(user)

    def remove_member(self, user):
        """Remove a member from the team."""
        self.members.remove(user)

    @classmethod
    def create_with_owner(cls, name, owner):
        """Create a new team and add the owner as a member."""
        team = cls.objects.create(name=name, owner=owner)
        team.members.add(owner)
        return team

class Invitation(models.Model):
    team = models.ForeignKey('Team', on_delete=models.CASCADE, db_index=True, related_name='invitations')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invitations')
    created_at = models.DateTimeField(auto_now_add=True ,db_index=True)
    expires_in_days = models.PositiveSmallIntegerField(default=3)

    def is_expired(self):
        expiration_date = self.created_at + dt.timedelta(days=self.expires_in_days)
        return timezone.now() > expiration_date

    def __str__(self):
        return f"Invitation created at {self.created_at}, expires in {self.expires_in_days} days"

    def get_invitation_url(self):
        return reverse('invitation_detail', kwargs={'pk': self.pk})
