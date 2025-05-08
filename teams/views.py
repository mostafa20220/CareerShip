from django.db.models import Count, F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Invitation
from teams.models import Team  # Assuming you have a Team model
from users.models import User  # Assuming you have a User model
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics

from .permissions import CanViewTeam, IsTeamAdmin, IsTeamMember
from .serializers import TeamSerializer, LeaveTeamSerializer, TeamDetailSerializer,  \
    CreateInvitationSerializer,InvitationDetailSerializer

from .models import TeamUser
from .services import is_team_member, add_team_member, remove_user_from_team, InvitationService, is_max_team_size


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

        team = serializer.validated_data['team']
        user = request.user
        remove_user_from_team(user=user, team=team)

        return Response({"message": "You have successfully left the team."}, status=status.HTTP_200_OK)



class TeamDetailView(generics.RetrieveUpdateAPIView):
    """
        API endpoint to retrieve and update team details.
        - GET: Retrieve team details.
        - PUT: Update team details.
    """
    queryset = Team.objects.all()
    serializer_class = TeamDetailSerializer
    permission_classes = [IsAuthenticated, CanViewTeam]  # Only authenticated users can access
    lookup_field = "pk"  # Retrieve by team ID

    def get_permissions(self):
        """
        Add IsTeamAdmin permission for update method only.
        """
        permissions = super().get_permissions()
        if self.request.method == "PATCH":
            # Add IsTeamAdmin permission for PATCH method
            permissions.append(IsTeamAdmin())
        return permissions



class GenerateInviteView(generics.CreateAPIView):
    """API endpoint to generate an invitation link for a team."""
    serializer_class = CreateInvitationSerializer
    permission_classes = [IsAuthenticated , IsTeamMember]

    def perform_create(self, serializer):
        """Attach the team from the URL parameter and ensure the user is authorized."""
        team_id = self.kwargs['pk']
        team = get_object_or_404(Team, id=team_id)

        serializer.save(team=team)


class InvitationDetailView(generics.RetrieveAPIView):
    """API endpoint for retrieving a single invitation."""
    queryset = Invitation.objects.all()
    serializer_class = InvitationDetailSerializer
    permission_classes = [IsAuthenticated]


class AcceptInvitationView(generics.GenericAPIView):
    """API endpoint to accept an invitation and join a team."""
    permission_classes = [IsAuthenticated]

    def post(self, request, invite_id):
        """Accepts an invitation and adds the user to the team."""
        invitation = get_object_or_404(Invitation, id=invite_id)

        try:
            # Use the service class to handle the invitation acceptance logic
            result = InvitationService.accept_invitation(invitation, request.user)
            return Response(result, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)
          
          
class ListTeams(generics.ListAPIView):
    """API endpoint to return a paginated response of all teams that are public and not full"""

    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        """Filter teams that are private or full"""
        return (
            Team.objects.filter(is_private=False)
            .annotate(member_count=Count('team_users'))
            .filter(member_count__lt=F('team_projects__project__max_team_size'))
        )
