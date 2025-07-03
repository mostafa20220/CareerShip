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
        'Category',
        on_delete=models.CASCADE,
        db_index=True,
        related_name='projects'
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='created_projects',
        db_index=True,
        null=True,
        blank=True
    )
    is_public = models.BooleanField(default=True, db_index=True)
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


class TeamProject(models.Model):
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, db_index=True)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, db_index=True)
    is_finished = models.BooleanField(default=False)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deployment_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Team Project'
        verbose_name_plural = 'Team Projects'
        constraints = [
            models.CheckConstraint(
                check=models.Q(is_finished=True, finished_at__isnull=False) | models.Q(is_finished=False, finished_at__isnull=True),
                name='finished_at_check'
            ),
            models.UniqueConstraint(fields=['team', 'project'], name='unique_team_project')
        ]
    def __str__(self):
        return f"{self.team.name} - {self.project.name} ({'Finished' if self.is_finished else 'In Progress'})"
