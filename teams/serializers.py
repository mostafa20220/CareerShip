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
