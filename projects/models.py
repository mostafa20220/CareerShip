from django.db import models

from django.utils.text import slugify


class DifficultyLevel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self ):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self ):
        return self.name


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
        self.slug = slugify(self.name)
        super(Project, self).save(*args, **kwargs)


class Task(models.Model):
    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE, db_index=True, related_name="tasks"
    )
    difficulty_level = models.ForeignKey(
        'DifficultyLevel',
        on_delete=models.CASCADE,
        db_index=True,
        related_name='tasks',
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    duration_in_days = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)


class Prerequisite(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()


class TaskPrerequisite(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, db_index=True)
    prerequisite = models.ForeignKey(
        'Prerequisite', on_delete=models.CASCADE, db_index=True,related_name='tasks'
    )


class Endpoint(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, db_index=True)
    method = models.CharField(max_length=10)
    path = models.TextField()
    description = models.TextField(blank=True, null=True)


class Submission(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, db_index=True, related_name='submissions')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, db_index=True, related_name="submissions")
    team = models.ForeignKey(
        'teams.Team', on_delete=models.CASCADE, null=True, blank=True, db_index=True,related_name='submissions'
    )
    is_pass = models.BooleanField(default=False)
    feedback = models.TextField(blank=True, null=True)
    # TODO: one of the following fields should be filled based on the project track or field.
    deployment_url = models.URLField(null=True, blank=True)
    github_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class UserProject(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, db_index=True)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, db_index=True)
    is_finished = models.BooleanField(default=False)
    deployment_url = models.URLField(blank=True, null=True)
