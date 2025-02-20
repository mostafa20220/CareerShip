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


class CreateTeamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Creates a new team and adds the creator as a member."""
        team_name = request.data.get("name")
        is_private = request.data.get("is_private") or True
        project = request.data.get("project")

        if not team_name:
            return Response({"error": "Team name is required"}, status=status.HTTP_400_BAD_REQUEST)


        # Create the team
        team = Team.objects.create(
            name=team_name,
            created_by=request.user,
            is_private=is_private,
        )

        # Add the creator as a member
        TeamUser.objects.create(team=team, user=request.user)

        return Response({
            "message": "Team created successfully",
            "team_id": team.id,
            "team_name": team.name
        }, status=status.HTTP_201_CREATED)