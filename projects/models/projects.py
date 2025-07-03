from symtable import Class

from django.db import models
from django.utils.text import slugify

class Category(models.TextChoices):
    FRONTEND = 'FRONTEND', 'Frontend'
    BACKEND = 'BACKEND', 'Backend'
    CONSOLE = 'CONSOLE', 'Console'
    OTHER = 'OTHER', 'Other'

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


# For frontend
class TaskReferenceImage(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='reference_images')
    image = models.ImageField(upload_to='reference_images/')
    viewport_width = models.PositiveIntegerField(default=1920)
    viewport_height = models.PositiveIntegerField(default=1080)
    description = models.CharField(max_length=255, blank=True , null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Project Reference Image'
        verbose_name_plural = 'Project Reference Images'

    def device_type(self):
        width = self.viewport_width

        if width < 768:
            return "Mobile"
        elif 768 <= width < 1024:
            return "Tablet"
        elif 1024 <= width < 1440:
            return "Laptop"
        else:
            return "Desktop"


class ScreenshotComparison(models.Model):
    team_project = models.ForeignKey('TeamProject', on_delete=models.CASCADE, related_name='screenshot_comparisons')
    reference_image = models.ForeignKey('TaskReferenceImage', on_delete=models.CASCADE)
    screenshot = models.ImageField(upload_to='screenshots/')
    similarity_score = models.FloatField(null=True, blank=True)  # 0.0 to 1.0
    comparison_image = models.ImageField(upload_to='comparison_results/', null=True, blank=True)
    feedback_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    COMPARISON_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('ERROR', 'Error'),
    ]
    status = models.CharField(max_length=10, choices=COMPARISON_STATUS_CHOICES, default='PENDING')

    class Meta:
        verbose_name = 'Screenshot Comparison'
        verbose_name_plural = 'Screenshot Comparisons'
