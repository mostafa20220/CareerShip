from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404

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


class TeamManagementService:
    def __init__(self, user):
        self.user = user

    def add_member(self, team_pk, email):
        """Add a member to the team."""
        team = get_object_or_404(Team, pk=team_pk)
        user_to_add = get_object_or_404(User, email=email)

        logger.info(f"User {self.user.id} attempting to add user {user_to_add.id} to team {team.uuid}")

        # Check if the current user is the team owner
        if team.owner != self.user:
            logger.warning(f"User {self.user.id} is not the owner of team {team.uuid}")
            raise ValidationError("Only team owners can add members.")

        # Check if user is already in the team
        if is_team_member(user=user_to_add, team=team):
            logger.warning(f"User {user_to_add.id} is already a member of team {team.uuid}")
            raise ValidationError("This user is already a member of the team.")

        # Check if team is full for any project it's registered in
        team_projects = TeamProject.objects.filter(team=team)
        for team_project in team_projects:
            if team.members.count() >= team_project.project.max_team_size:
                logger.warning(f"Team {team.uuid} has reached its maximum size for project {team_project.project.id}.")
                raise ValidationError(f"This team has reached its maximum size for project '{team_project.project.name}'.")

        # Add the user to the team
        add_team_member(user=user_to_add, team=team)
        logger.info(f"User {user_to_add.id} successfully added to team {team.uuid}")

        return {"message": f"User {user_to_add.email} has been added to the team."}

    def remove_member(self, team_pk, email):
        """Remove a member from the team."""
        team = get_object_or_404(Team, pk=team_pk)
        user_to_remove = get_object_or_404(User, email=email)

        logger.info(f"User {self.user.id} attempting to remove user {user_to_remove.id} from team {team.uuid}")

        # Check if the current user is the team owner
        if team.owner != self.user:
            logger.warning(f"User {self.user.id} is not the owner of team {team.uuid}")
            raise ValidationError("Only team owners can remove members.")

        # Cannot remove the team owner
        if user_to_remove == team.owner:
            logger.warning(f"Attempted to remove team owner {team.owner.id} from team {team.uuid}")
            raise ValidationError("Cannot remove the team owner.")

        # Check if user is in the team
        if not is_team_member(user=user_to_remove, team=team):
            logger.warning(f"User {user_to_remove.id} is not a member of team {team.uuid}")
            raise ValidationError("This user is not a member of the team.")

        # Remove the user from the team
        remove_user_from_team(user=user_to_remove, team=team)
        logger.info(f"User {user_to_remove.id} successfully removed from team {team.uuid}")

        return {"message": f"User {user_to_remove.email} has been removed from the team."}

    def disable_invitation(self, invitation_id):
        invitation = get_object_or_404(Invitation, pk=invitation_id)
        team = invitation.team

        if team.owner != self.user:
            raise ValidationError("You are not the owner of this team.")

        invitation.is_active = False
        invitation.save()
        return {"message": "Invitation has been disabled."}

    def _get_team_and_check_ownership(self, team_id):
        team = get_object_or_404(Team, pk=team_id)
        if team.owner != self.user:
            raise ValidationError("You are not the owner of this team.")
        return team

    def _get_user_by_email(self, email):
        user = get_object_or_404(User, email=email)
        if not user.is_active:
            raise ValidationError("User is not active.")
        return user

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


def remove_user_from_team(user: User, team: Team):
    """Remove a user from a team."""
    logger.info(f"Removing user {user.id} from team {team.id}")
    team.remove_member(user)


def check_if_user_can_leave_team(user: User, team: Team):
    """Checks if a user is allowed to leave a team, user can't leave if they are not a team member , the admin of the team, only member of that team"""

    if not is_team_member(user=user, team=team):
        raise ValidationError("You are not a member of this team.")

    if team.members.count() == 1:
        if user.teams.count() == 1:
            # User is the only member of the team and has no other teams
            raise ValidationError("You are the only member of this team. And you have no other teams.")


    if is_user_team_admin(user=user, team=team) and team.members.count() > 1:
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
