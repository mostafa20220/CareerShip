from django.db import models
from django.conf import settings
from django.urls import reverse
import datetime as dt
from django.utils import timezone
import uuid

class Team(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_teams')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"

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

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'
        constraints = [
            models.UniqueConstraint(fields=['name', 'owner'], name='unique_team_name_per_owner')
        ]

class Invitation(models.Model):
    uuid = models.CharField(max_length=36, unique=True, default=uuid.uuid4)
    team = models.ForeignKey('Team', on_delete=models.CASCADE, db_index=True, related_name='invitations')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invitations')
    created_at = models.DateTimeField(auto_now_add=True ,db_index=True)
    expires_in_days = models.PositiveSmallIntegerField(default=3)
    is_active = models.BooleanField(default=True)

    def is_expired(self):
        expiration_date = self.created_at + dt.timedelta(days=self.expires_in_days)
        return timezone.now() > expiration_date

    def __str__(self):
        return f"Invitation created at {self.created_at}, expires in {self.expires_in_days} days"

    def get_invitation_url(self):
        return reverse('team-invitations-detail', kwargs={'team_pk': self.team.uuid, 'pk': self.uuid})
