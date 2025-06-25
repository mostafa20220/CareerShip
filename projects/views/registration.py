from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from projects.models.projects import UserProject
from projects.serializers import UserProjectSerializer, ProjectRegistrationSerializer
from utils.logging_utils import get_logger

logger = get_logger(__name__)

class ProjectRegistrationViewSet(viewsets.ModelViewSet):
    """
    A viewset for handling project registrations.
    - list: Returns a list of projects the current user is registered for.
    - create: Registers the current user for a new project.
    - destroy: Cancels the user's registration for a project.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """This view should return a list of all the project registrations for the currently authenticated user."""
        logger.info(f"User {self.request.user.id} fetching their registered projects.")
        return UserProject.objects.filter(user=self.request.user).select_related('project')

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectRegistrationSerializer
        return UserProjectSerializer

    def perform_create(self, serializer):
        logger.info(f"User {self.request.user.id} registering for project {serializer.validated_data['project'].id}")
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.info(f"User {request.user.id} canceling registration for project {instance.project.id}")
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
