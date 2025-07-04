from django.db import models
from users.models import User



class DraftStatus(models.TextChoices):
    GENERATING = 'generating', 'Generating'
    PENDING_REVIEW = 'pending_review', 'Pending Review'
    COMPLETED = 'completed', 'Completed'
    ARCHIVED = 'archived', 'Archived'


class ProjectDraft(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey("Category", on_delete=models.CASCADE)
    difficulty_level = models.ForeignKey("DifficultyLevel", on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=255, blank=True, null=True, default=f"New Project Draft")
    is_public = models.BooleanField(default=False)
    conversation_history = models.JSONField(default=list, blank=True)
    latest_project_json = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=DraftStatus.choices, default=DraftStatus.GENERATING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ProjectDraft for {self.user.email} at {self.created_at}"
