from dataclasses import fields

from django.urls import reverse
from rest_framework import serializers

from projects.serializers import ProjectSerializer
from teams.models import Team, TeamUser,  Invitation
from projects.models import Project
from users.serializers import RetrieveProfileSerializer
from .services import *
from django.core.exceptions import ValidationError as DjangoValidationError

class TeamSerializer(serializers.ModelSerializer):

    project_id = serializers.PrimaryKeyRelatedField(required=True, queryset=Project.objects.all(), write_only=True)
    admin = serializers.HiddenField(default=serializers.CurrentUserDefault())


    class Meta:
        model = Team
        fields = ["id" , "name" , "is_private", "created_at" , "project_id", "admin"]
        read_only_fields = ["id","admin"]





    def create(self, validated_data):
        """Creates a new team and automatically adds the creator as a member."""
        user = self.context['request'].user
        project = validated_data.pop('project_id')
        team_name = validated_data.pop('name')


        # Check if the user has an ACTIVE team for this project.
        if is_user_on_active_team_for_project(user,project):
            raise serializers.ValidationError(
                {"error": "You are already part of an Active team for this project."}
            )

        # create the team
        team = create_team(team_name=team_name , user=user, project=project)
        return  team

class LeaveTeamSerializer(serializers.Serializer):
    team = serializers.PrimaryKeyRelatedField(required=True, queryset=Team.objects.all(), write_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())


    def validate(self, attrs):
        user = attrs.get('user')
        team = attrs.get('team')

        try:
            check_if_user_can_leave_team(user=user, team=team)
        except ValidationError as e:

            raise serializers.ValidationError({"error": e.args[0]})

        return attrs





class TeamDetailSerializer(serializers.ModelSerializer):

   project = serializers.SerializerMethodField()
   users = serializers.SerializerMethodField()

   class Meta:
       model = Team
       fields = ["id" , "name", "is_private", "active" , "admin" ,  "project" , "users"]

   def get_users(self, obj):
       team_users = TeamUser.objects.filter(team=obj).select_related("user")
       return RetrieveProfileSerializer([tu.user for tu in team_users] , many=True).data

   def get_project(self, obj):
       project = obj.project
       # Serialize only the id instead of using ProjectSerializer which returns all project tasks ...
       return {
           "id": project.id,
           "name": project.name
       }



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


class UpdateTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["name", "is_private"]

