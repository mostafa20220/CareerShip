from django.core.exceptions import ValidationError

from teams.models import TeamUser, Team



from rest_framework.exceptions import ValidationError
from .models import Invitation



class InvitationService:
    """Service to handle the logic of accepting an invitation and adding a user to the team."""

    @staticmethod
    def accept_invitation(invitation, user):
        """Accept an invitation and add the user to the team."""

        if not invitation:
            raise ValidationError("Invitation not found.")

        # Check if invitation is expired
        if invitation.is_expired():
            raise ValidationError("Invitation has expired.")

        # Check if user is already in the team
        if is_team_member(team=invitation.team, user=user):
            raise ValidationError("You are already a member of this team.")
          
        if is_max_team_size(team=invitation.team, project=invitation.team.project):
            raise ValidationError("This team has reached its maximum size.")

        # Add the user to the team
        add_team_member(team=invitation.team, user=user)

        return {"error": "You have successfully joined the team."}
      




def is_max_team_size(team, project):
    """Checks if a team size exceeds the maximum team size of a project"""
    return TeamUser.objects.filter(team=team).count() >= project.max_team_size



def is_team_member(user, team):
    """Check if a user is a member of a given team."""
    return TeamUser.objects.filter(team=team, user=user).exists()



def get_user_teams_for_project(user, project):
    """returns the teams that the user is in for this project."""
    return TeamUser.objects.filter(team__project=project, user=user)



def is_user_on_active_team_for_project(user, project):
    """Check if a user is on a team for a given project."""
    return get_user_teams_for_project(user,project).filter(team__active=True).exists()


def is_user_team_admin(user, team):
    """Check if a user is a team admin for a given team."""
    if not user or not team:
        return False
    return team.admin == user


def team_members(team):
    return TeamUser.objects.filter(team=team)



def add_team_member(user, team):
    """Add a user to a team in this project."""
    TeamUser.objects.create(team=team, user=user)

def create_team(team_name , user , project):
    """Create a team for this project."""
    team = Team.objects.create(name=team_name, admin=user , project=project)
    # link the created team with the user and the project
    TeamUser.objects.create(team=team, user=user)

    return team


def remove_user_from_team(user, team):
    """Remove a user from a team."""
    TeamUser.objects.filter(team=team, user=user).delete()


def check_if_user_can_leave_team(user, team):
    """Checks if a user is allowed to leave a team, user can't leave if they are not a team member , the admin of the team, only member of that team"""

    if not is_team_member(user, team=team):
        raise ValidationError("You are not a member of this team.")

    if team_members(team).count() == 1:
        raise ValidationError(
            "You are the only member of this team. If you want to leave, please delete the team instead."
        )

    if is_user_team_admin(user=user, team=team):
        raise ValidationError(
            "You are the admin of this team. To leave, you must first assign admin rights to another team member")

