from rest_framework import serializers
from teams.models import Team, TeamUser


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id" , "name" , "is_private" , "project"]
        # read_only_fields = ("id","created_at","created_by")

    def create(self, validated_data):
        """Creates a new team and automatically adds the creator as a member."""
        user = self.context['request'].user # get the logged in user
        project = validated_data['project']
        team = Team.objects.create(created_by=user, project=project , **validated_data)
        return  team
