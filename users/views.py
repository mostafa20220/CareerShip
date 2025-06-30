from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from users.serializers import (
    LogoutSerializer,
    RegisterSerializer,
    RetrieveProfileSerializer,
    UpdateProfileSerializer,
    SkillsSerializer,
    UserSkillsSerializer,
)
from users.models import Skill, UserSkills


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer


class LogoutView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = RetrieveProfileSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = UpdateProfileSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        serializer = UpdateProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:8000/api/v1/auth/accounts/google/login/callback/"
    client_class = OAuth2Client


class GitHubLoginView(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = "http://localhost:8000/api/v1/auth/accounts/github/login/callback/"
    client_class = OAuth2Client


class SkillsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        skills = Skill.objects.all()
        serializer = SkillsSerializer(skills, many=True)
        return Response(serializer.data)


class UserSkillsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_skills = UserSkills.objects.filter(user=user)
        serializer = UserSkillsSerializer(user_skills, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        skill_id = request.data.get('skill_id')
        if not skill_id:
            return Response(
                {'detail': 'skill_id is required.'}, status=status.HTTP_400_BAD_REQUEST
            )
        skill = Skill.objects.get(id=skill_id)

        user_skill, created = UserSkills.objects.get_or_create(user=user, skill=skill)
        if not created:
            return Response(
                {'detail': 'Skill already added.'}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response({'detail': 'Skill added.'}, status=status.HTTP_201_CREATED)

    def delete(self, request, skill_id=None):
        user = request.user
        user_skill = UserSkills.objects.get(user=user, skill_id=skill_id)
        user_skill.delete()
        return Response(
            {'detail': 'Skill removed.'}, status=status.HTTP_204_NO_CONTENT
        )

