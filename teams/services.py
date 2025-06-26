from rest_framework.exceptions import ValidationError

from teams.models import Invitation, Team
from projects.models.projects import TeamProject, Project
from users.models import User
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class InvitationService:
    """Service to handle the logic of accepting an invitation and adding a user to the team."""

    @staticmethod
    def accept_invitation(invitation: Invitation, user: User):
        """Accept an invitation and add the user to the team."""
        logger.info(f"User {user.id} attempting to accept invitation {invitation.id}")

        if not invitation:
            logger.warning(f"Invitation not found for user {user.id}")
            raise ValidationError("Invitation not found.")

        # Check if invitation is expired
        if invitation.is_expired():
            logger.warning(f"Invitation {invitation.id} has expired.")
            raise ValidationError("Invitation has expired.")

        team = invitation.team
        # Check if user is already in the team
        if is_team_member(user=user, team=team):
            logger.warning(f"User {user.id} is already a member of team {team.id}")
            raise ValidationError("You are already a member of this team.")

        # Check if team is full for any project it's registered in
        team_projects = TeamProject.objects.filter(team=team)
        for team_project in team_projects:
            if team.members.count() >= team_project.project.max_team_size:
                logger.warning(f"Team {team.id} has reached its maximum size for project {team_project.project.id}.")
                raise ValidationError(f"This team has reached its maximum size for project '{team_project.project.name}'.")

        # Add the user to the team
        add_team_member(user=user, team=team)
        logger.info(f"User {user.id} successfully joined team {team.id}")

        return {"message": "You have successfully joined the team."}


def is_max_team_size(team: Team, project: Project):
    """Checks if a team size exceeds the maximum team size of a project"""
    return team.members.count() >= project.max_team_size


def is_team_member(user: User, team: Team):
    """Check if a user is a member of a given team."""
    return team.members.filter(pk=user.pk).exists()


def get_user_teams_for_project(user: User, project: Project):
    """returns the teams that the user is in for this project."""
    return Team.objects.filter(members=user, teamproject__project=project)


def is_user_on_active_team_for_project(user: User, project: Project):
    """Check if a user is on a team for a given project."""
    return TeamProject.objects.filter(team__members=user, project=project, is_finished=False).exists()


def is_user_team_admin(user: User, team: Team):
    """Check if a user is a team admin for a given team."""
    if not user or not team:
        return False
    return team.owner == user


def team_members(team: Team):
    return team.members.all()


def add_team_member(user: User, team: Team):
    """Add a user to a team in this project."""
    logger.info(f"Adding user {user.id} to team {team.id}")
    team.add_member(user)


def create_team(team_name: str, user: User, project: Project):
    """Create a team and register it for a project."""
    logger.info(f"User {user.id} creating team '{team_name}' for project {project.id}")
    team = Team.create_with_owner(name=team_name, owner=user)
    TeamProject.objects.create(team=team, project=project)
    logger.info(f"Team {team.id} created successfully.")
    return team


def remove_user_from_team(user: User, team: Team):
    """Remove a user from a team."""
    logger.info(f"Removing user {user.id} from team {team.id}")
    team.remove_member(user)


def check_if_user_can_leave_team(user: User, team: Team):
    """Checks if a user is allowed to leave a team, user can't leave if they are not a team member , the admin of the team, only member of that team"""

    if not is_team_member(user=user, team=team):
        raise ValidationError("You are not a member of this team.")

    if team.members.count() == 1:
        raise ValidationError(
            "You are the only member of this team. If you want to leave, please delete the team instead."
        )

    if is_user_team_admin(user=user, team=team):
        raise ValidationError(
            "You are the admin of this team. To leave, you must first assign admin rights to another team member")


def change_team_admin(team: Team, new_admin: User):
    """Change the admin of a team."""
    if not is_team_member(team=team, user=new_admin):
        raise ValidationError("The user is not a member of this team.")

    if team.owner == new_admin:
        raise ValidationError("You are already the admin of this team.")

    team.owner = new_admin
    team.save()
    return team
