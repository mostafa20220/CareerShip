from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from projects.models.projects import TeamProject
from projects.serializers import TeamProjectSerializer, ProjectRegistrationSerializer
from utils.logging_utils import get_logger

logger = get_logger(__name__)

class ProjectRegistrationViewSet(viewsets.ModelViewSet):
    """
    A viewset for handling project registrations for teams.
    - list: Returns a list of projects the current user's teams are registered for.
    - create: Registers a team for a new project.
    - destroy: Cancels a team's registration for a project.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectRegistrationSerializer
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        user = self.request.user
        return TeamProject.objects.filter(team__in=user.teams.all())

    def get_serializer_class(self):
        if self.action == 'list':
            return TeamProjectSerializer
        return ProjectRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
