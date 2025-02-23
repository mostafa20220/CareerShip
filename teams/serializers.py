from rest_framework import serializers
from teams.models import Team, TeamUser, TeamProject
from projects.models import Project

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
        if TeamUser.objects.filter(team__team_projects__project=project, user=user).exists():
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
        if not TeamUser.objects.filter(team=team, user=user).exists():
            raise serializers.ValidationError("You are not a member of this team.")

        # Check if the user is the only member
        #if TeamUser.objects.filter(team=team).count() == 1:
            # raise serializers.ValidationError("You cannot leave because you are the only member.")

        # Check if the user is the team creator
        #if team.created_by == user:
            # raise serializers.ValidationError("You cannot leave as the team creator. Transfer ownership first.")

        return value