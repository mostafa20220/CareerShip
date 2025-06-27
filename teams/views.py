from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import Invitation, Team
from .permissions import IsTeamAdmin
from .serializers import (
    InvitationSerializer,
    TeamDetailSerializer,
    MemberEmailSerializer,
    TeamSerializer,
)
from .services import InvitationService, TeamManagementService, check_if_user_can_leave_team, remove_user_from_team


class TeamViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing team instances.
    """
    queryset = Team.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'uuid'
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return TeamDetailSerializer
        return TeamSerializer

    def get_queryset(self):
        return self.request.user.teams.all()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'add_member', 'remove_member', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsTeamAdmin]
        return super().get_permissions()

    @action(detail=True, methods=['post', 'delete'])
    def members(self, request, uuid=None):
        team = self.get_object()

        serializer = MemberEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        service = TeamManagementService(user=request.user)
        if request.method == 'POST':
            result = service.add_member(team_pk=team.pk, email=email)
            return Response(result)

        elif request.method == 'DELETE':
            result = service.remove_member(team_pk=team.pk, email=email)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return None

    @action(detail=True, methods=['post'], url_path='leave')
    def leave(self, request, uuid=None):
        """
        Allow a user to leave a team.
        """
        team = self.get_object()
        user = request.user

        try:
            # Check if user can leave the team
            check_if_user_can_leave_team(user=user, team=team)

            # Remove user from team
            remove_user_from_team(user=user, team=team)

            # If the team is empty after the user leaves, delete it
            if team.members.count() == 0:
                team.delete()
                return Response(
                    {"message": "You have successfully left the team. The team has been deleted as it was empty."},
                    status=status.HTTP_200_OK
                )

            return Response(
                {"message": "You have successfully left the team."},
                status=status.HTTP_200_OK
            )

        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class InvitationViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing team invitations.
    Accessed through: /teams/{team_pk}/invitations/
    """
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'pk'  # Corrected from team_pk

    def get_queryset(self):
        team_uuid = self.kwargs.get('team_pk')
        if team_uuid is None:
            return Invitation.objects.none()
        return Invitation.objects.filter(team__uuid=team_uuid)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        team_uuid = self.kwargs.get('team_pk')
        if team_uuid:
            context['team'] = get_object_or_404(Team, uuid=team_uuid)
        return context

    def perform_create(self, serializer):
        team_uuid = self.kwargs.get('team_pk')
        team = get_object_or_404(Team, uuid=team_uuid)

        # Check if user is team owner
        if team.owner != self.request.user:
            raise ValidationError("Only team owners can create invitations.")

        serializer.save(team=team, created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def accept(self, request, team_pk=None, pk=None):
        """Accept an invitation to join the team."""
        invitation = self.get_object()

        # Check if invitation is still active
        if not invitation.is_active:
            return Response(
                {"error": "This invitation has been disabled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = InvitationService.accept_invitation(invitation=invitation, user=request.user)
        return Response(result)

    @action(detail=True, methods=['post'])
    def disable(self, request, team_pk=None, pk=None):
        """Disable an invitation (only team owner can do this)."""
        invitation = self.get_object()
        team = invitation.team

        if team.owner != request.user:
            return Response(
                {"error": "Only team owners can disable invitations."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not invitation.is_active:
            return Response(
                {"error": "This invitation is already disabled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.is_active = False
        invitation.save()

        return Response({"message": "Invitation has been disabled."})

    @action(detail=True, methods=['post'])
    def enable(self, request, team_pk=None, pk=None):
        """Enable an invitation (only team owner can do this)."""
        invitation = self.get_object()
        team = invitation.team

        if team.owner != request.user:
            return Response(
                {"error": "Only team owners can enable invitations."},
                status=status.HTTP_403_FORBIDDEN
            )

        if invitation.is_active:
            return Response(
                {"error": "This invitation is already enabled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.is_active = True
        invitation.save()

        return Response({"message": "Invitation has been enabled."})