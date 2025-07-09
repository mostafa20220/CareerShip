from teams.models import Team
from users.models import User, Skill, UserSkills
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['first_name','last_name','email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_password(self, value):
        try:
            django_validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user



class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def validate_refresh(self, value):
        try:
            token = RefreshToken(value)
            token.blacklist()  # Blacklist the refresh token
        except Exception as e:
            raise serializers.ValidationError("Invalid or expired refresh token.")

        return value

    def create(self, validated_data):
        return validated_data

class RetrieveProfileSerializer(serializers.ModelSerializer):
    teams = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = [ 'id' , 'first_name','last_name','email','user_type','is_premium','phone','avatar','teams']
    def get_teams(self, obj):
#         return all user joined teams serialized date
        from teams.serializers import TeamSerializer
        teams = Team.objects.filter(members=obj)
        return TeamSerializer(teams, many=True).data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [ 'id' , 'first_name','last_name','email','user_type','is_premium','phone','avatar']

class UpdateProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['first_name','last_name','phone','avatar', ]

class RemoveUserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    
    def validate(self, data):
        user = User.objects.filter(email=data.get('email'),id=data.get("id")).first()
        if not user:
            raise serializers.ValidationError("User with this email and id does not exist.")
        data['user'] = user
        return data

    def create(self, validated_data):
        user = validated_data.get('user')
        user.is_active = False
        user.save()
        return user


class SkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']


class UserSkillsSerializer(serializers.ModelSerializer):
    skill_id = serializers.IntegerField(source='skill.id')
    skill_name = serializers.CharField(source='skill.name')

    class Meta:
        model = UserSkills
        fields = ['skill_id', 'skill_name']
