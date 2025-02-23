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

from .serializers import TeamSerializer, LeaveTeamSerializer


class InvitationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        invitation = get_object_or_404(Invitation, pk=pk)
        return Response({
            "id": invitation.id,
            "team": invitation.team.name,
            "created_by": invitation.created_by.username,
            "created_at": invitation.created_at,
            "expires_in_days": invitation.expires_in_days,
            "is_expired": invitation.is_expired(),
        })

from .models import TeamUser
class AcceptInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        invitation = get_object_or_404(Invitation, pk=pk)

        if invitation.is_expired():
            return Response({"error": "Invitation has expired"}, status=status.HTTP_400_BAD_REQUEST)
        team = invitation.team

        # Add user to the team
        TeamUser(team=team, user=self.request.user).save()


        return Response({"message": "Invitation accepted successfully!"}, status=status.HTTP_200_OK)


# class CreateInvitationView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request, team_id):
#


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
