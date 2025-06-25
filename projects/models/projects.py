from django.db import models
from django.utils.text import slugify


class Project(models.Model):
    difficulty_level = models.ForeignKey(
        'DifficultyLevel',
        on_delete=models.CASCADE,
        db_index=True,
        related_name='projects',
    )
    category = models.ForeignKey(
        'Category', on_delete=models.CASCADE,  db_index=True, related_name='projects'
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    is_premium = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    max_team_size = models.PositiveSmallIntegerField(default=1)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate slug from name if not provided
            self.slug = slugify(self.name)
        super(Project, self).save(*args, **kwargs)

    def __str__(self ):
        return self.name


class UserProject(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, db_index=True)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, db_index=True)
    is_finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deployment_url = models.URLField(blank=True, null=True)
