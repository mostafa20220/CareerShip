from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView, ListAPIView

from users.permissions import IsAdmin
from utils.pagination import StandardPagination
from django.shortcuts import get_object_or_404
import uuid


from certificates.models import Certificate
from projects.models.projects import Project, TeamProject
from projects.serializers import (
    ProjectSeedSerializer,
    ProjectSerializer,
    ProjectDetailsSerializer,
)
from projects.services import ProjectSeederService, ProjectCreationError
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class ProjectsListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        difficulty_level = self.request.query_params.get('difficulty_level')

        if category:
            queryset = queryset.filter(category__name=category)
        if difficulty_level:
            queryset = queryset.filter(difficulty_level__name=difficulty_level)

        return queryset


class ProjectDetailsView(RetrieveAPIView):
    lookup_url_kwarg = 'project_id'
    queryset = Project.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectDetailsSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_certificate(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    user_project = TeamProject.objects.filter(
        user=request.user, project=project, is_finished=True
    ).first()
    if not user_project:
        return Response(
            {"detail": "Project not finished by user."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if Certificate.objects.filter(user=request.user, project=project).exists():
        return Response(
            {"detail": "Certificate already issued."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    cert = Certificate.objects.create(
        user=request.user, project=project, no=uuid.uuid4()
    )
    return Response(
        {
            "detail": "Certificate requested successfully.",
            "certificate_id": str(cert.no),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def certificate_available(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    user_project = TeamProject.objects.filter(
        user=request.user, project=project, is_finished=True
    ).first()
    if not user_project:
        return Response(
            {"available": False, "detail": "Project not finished by user."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    certificate = Certificate.objects.filter(
        user=request.user, project=project
    ).exists()
    if certificate:
        return Response(
            {"available": False, "detail": "Certificate already issued."},
            status=status.HTTP_200_OK,
        )
    return Response(
        {"available": True, "detail": "Certificate is available to be requested."},
        status=status.HTTP_200_OK,
    )


class ProjectSeedUploadView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        logger.info(
            f"Received project seed upload request from user id: {request.user.id}, user name: {request.user.first_name} {request.user.last_name}"
        )
        logger.debug(f"Request data: {request.data}")
        serializer = ProjectSeedSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            service = ProjectSeederService(serializer.validated_data)
            project = service.create_project()

        except ValidationError as e:
            logger.warning(f"Validation error during project seed upload: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except ProjectCreationError as e:
            logger.error(f"Project creation error during project seed upload: {e}")
            return Response({'error': str(e)}, status=e.status_code)
        except Exception as e:
            logger.critical(
                f"Unexpected error during project seed upload: {e}", exc_info=True
            )
            # Catch unexpected errors
            return Response(
                {'error': f'An unexpected error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # On success, return a representation of the created project's main details
        response_data = {
            'id': project.id,
            'name': project.name,
            'slug': project.slug,
            'message': 'Project created successfully.',
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
