from django.shortcuts import render

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Invitation
from teams.models import Team  # Assuming you have a Team model
from users.models import User  # Assuming you have a User model
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics

from .serializers import TeamSerializer, LeaveTeamSerializer, TeamDetailSerializer,  \
    InvitationSerializer

from .models import TeamUser
from .services import is_team_member, add_team_member


class TeamDetailView(generics.RetrieveAPIView):
    """API endpoint to retrieve team details along with project name and team members."""
    queryset = Team.objects.all()
    serializer_class = TeamDetailSerializer
    permission_classes = [IsAuthenticated]  # Only authenticated users can access
    lookup_field = "pk"  # Retrieve by team ID


class CreateTeamView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LeaveTeamView(APIView):
    """Allows a user to leave a team."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LeaveTeamSerializer(data=request.data, context={'request': request})

        # Run serializer validation
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get validated team_id
        team_id = serializer.validated_data['team_id']
        user = request.user

        # Remove the user from the team
        TeamUser.objects.filter(team_id=team_id, user=user).delete()

        return Response({"message": "You have successfully left the team."}, status=status.HTTP_200_OK)



class GenerateInviteView(generics.CreateAPIView):
    """API endpoint to generate an invitation link for a team."""
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Limit queryset to invitations for the specified team."""
        team_id = self.kwargs["team_id"]
        return Invitation.objects.filter(team_id=team_id)

    def get_serializer_context(self):
        """Pass additional context to serializer."""
        context = super().get_serializer_context()
        team_id = self.kwargs["pk"]
        team = get_object_or_404(Team, id=team_id)
        context["team"] = team  # ✅ Fix: Pass team instance
        return context

    def perform_create(self, serializer):
        """Attach the team from the URL parameter and ensure the user is authorized."""
        team = self.get_serializer_context()["team"]
        serializer.save(team=team, created_by=self.request.user)


class InvitationDetailView(generics.RetrieveAPIView):
    """API endpoint for retrieving a single invitation."""
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]

class AcceptInvitationView(generics.GenericAPIView):
    """API endpoint to accept an invitation and join a team."""
    permission_classes = [IsAuthenticated]

    def post(self, request, invite_id):
        """Accepts an invitation and adds the user to the team."""
        invitation = get_object_or_404(Invitation, id=invite_id)

        # Check if invitation is expired
        if invitation.is_expired():
            return Response({"error": "Invitation has expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user is already in the team
        if is_team_member(team=invitation.team,user=request.user):
            return Response({"error": "You are already a member of this team."}, status=status.HTTP_400_BAD_REQUEST)

        # Add user to the team
        add_team_member(team=invitation.team, user=request.user)

        return Response({"message": "You have successfully joined the team."}, status=status.HTTP_200_OK)