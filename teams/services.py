from teams.models import TeamUser


def is_team_member(user, team):
    """Check if a user is a member of a given team."""
    return TeamUser.objects.filter(team=team, user=user).exists()



def user_team_for_project(user, project):
    """Check if a user is a member of a team in this project."""
    return TeamUser.objects.filter(team__team_projects__project=project, user=user)


def add_team_member(user, team):
    """Add a user to a team in this project."""
    TeamUser.objects.create(team=team, user=user)
