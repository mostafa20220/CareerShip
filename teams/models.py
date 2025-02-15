from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

class TeamProject(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, db_index=True)
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, db_index=True)

class TeamUser(models.Model):
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, db_index=True)
