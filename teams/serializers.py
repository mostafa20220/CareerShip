from django.urls import reverse
from rest_framework import serializers
from teams.models import Team, TeamUser, TeamProject, Invitation
from projects.models import Project
from .services import *

class TeamSerializer(serializers.ModelSerializer):

    project_id = serializers.PrimaryKeyRelatedField(required=True, queryset=Project.objects.all(), write_only=True)
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())


    class Meta:
        model = Team
        fields = ["id" , "name" , "is_private", "created_at" , "project_id", "created_by"]
        read_only_fields = ["id","created_at"]





    def create(self, validated_data):
        """Creates a new team and automatically adds the creator as a member."""
        user = self.context['request'].user
        project = validated_data.pop('project_id')
        team_name = validated_data.pop('name')


        # ✅ Check if the user is already in a team for this project
        if user_team_for_project(user,project).exists():
            raise serializers.ValidationError(
                {"error": "You are already part of a team for this project."}
            )

        # create the team
        team = Team.objects.create(name=team_name,created_by=user)
        # link the created team with the user and the project
        TeamUser.objects.create(team=team , user=user)
        #project = Project.objects.get(id=project_id)
        TeamProject.objects.create(team=team , project=project)
        return  team

class LeaveTeamSerializer(serializers.Serializer):
    team_id = serializers.IntegerField(required=True)

    def validate_team_id(self, value):
        """Ensure the team exists and the user is a member before leaving."""
        user = self.context['request'].user

        # Check if the team exists
        try:
            team = Team.objects.get(id=value)
        except Team.DoesNotExist:
            raise serializers.ValidationError("Team not found.")

        # Check if the user is in the team
        if not is_team_member(user, team):
            raise serializers.ValidationError("You are not a member of this team.")

        # Check if the user is the only member
        #if TeamUser.objects.filter(team=team).count() == 1:
            # raise serializers.ValidationError("You cannot leave because you are the only member.")

        # Check if the user is the team creator
        #if team.created_by == user:
            # raise serializers.ValidationError("You cannot leave as the team creator. Transfer ownership first.")

        return value




class TeamDetailSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ["id", "name", "is_private", "created_by", "created_at", "project_name", "users"]

    def get_project_name(self, obj):
        """Get the project name associated with this team."""
        team_project = obj.team_projects.first()  # Get the related project
        return team_project.project.name if team_project else None

    def get_users(self, obj):
        """Get a list of usernames in the team."""
        return [
            f"{team_user.user.first_name} {team_user.user.last_name}".strip()
            for team_user in obj.teams.select_related("user")
        ]










class InvitationSerializer(serializers.ModelSerializer):
    invitation_url = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = ["id", "created_by", "created_at", "expires_in_days", "invitation_url"]
        read_only_fields = ["created_by", "created_at", "invitation_url"]

    def validate(self, data):
        """Ensure the user is a member of the team before generating an invite."""
        user = self.context["request"].user
        team = self.context["team"]

        if not is_team_member(user, team):
            raise serializers.ValidationError("You are not a member of this team.")

        return data

    def get_invitation_url(self, obj):
        """Generate the invitation URL."""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(reverse("invitation-detail", kwargs={"pk": obj.pk}))
        return reverse("invitation-detail", kwargs={"pk": obj.pk})

    def create(self, validated_data):
        """Use the service function to create an invitation."""
        user = self.context["request"].user
        team = self.context["team"]
        return Invitation.objects.create(
            team=team,
            created_by=user,
        )


