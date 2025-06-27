from rest_framework import serializers
from .models import Team, Invitation
from users.models import User


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('uuid', 'name')
        lookup_field = 'uuid'
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'}
        }

    #     validate there is no team with the same name for the user
    def validate_name(self, value):
        user = self.context['request'].user
        if Team.objects.filter(name=value, owner=user).exists():
            raise serializers.ValidationError("A team with this name already exists.")
        return value

    def create(self, validated_data):
        owner = self.context['request'].user
        team = Team.create_with_owner(name=validated_data['name'], owner=owner)
        return team


class TeamDetailSerializer(serializers.ModelSerializer):
    owner = MemberSerializer(read_only=True)
    members = MemberSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ('uuid', 'name', 'owner', 'members', 'created_at')
        lookup_field = 'uuid'
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'}
        }


class InvitationSerializer(serializers.ModelSerializer):
    invitation_url = serializers.CharField(source='get_invitation_url', read_only=True)

    class Meta:
        model = Invitation
        fields = ('uuid', 'expires_in_days', 'is_active', 'invitation_url','created_at')
        read_only_fields = ('uuid', 'is_active', 'invitation_url')

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("User context is required")

        team = self.context.get('team')
        if not team:
            raise serializers.ValidationError("Team context is required")

        validated_data['team'] = team
        validated_data['created_by'] = request.user

        invitation = Invitation.objects.create(**validated_data)
        return invitation


class MemberEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value
