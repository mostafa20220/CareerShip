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
from projects.models.projects import Project
from projects.serializers import (
    ProjectSeedSerializer,
    ProjectSerializer,
    ProjectDetailsSerializer,
)
from projects.services.project_seed_service import ProjectCreationError, ProjectSeederService
from projects.services.project_filter_service import ProjectFilterService
from projects.services.query_parameter_parser import QueryParameterParser
from projects.services.certificate_service import CertificateService
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class ProjectsListView(ListAPIView):
    """List view for projects with advanced filtering capabilities."""

    permission_classes = [IsAuthenticated]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    pagination_class = StandardPagination

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_service = ProjectFilterService()
        self.query_parser = QueryParameterParser()

    def get_queryset(self):
        """Get filtered queryset based on query parameters."""
        filters = self.query_parser.extract_filters(self.request)
        return self.filter_service.get_filtered_projects(filters, self.request.user)

class UserCreatedProjectsView(ListAPIView):
    """List view for projects created by the authenticated user."""

    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Project.objects.filter(created_by=self.request.user)


class ProjectDetailsView(RetrieveAPIView):
    """Detail view for a specific project."""

    lookup_url_kwarg = 'project_id'
    queryset = Project.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectDetailsSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_certificate(request, project_id):
    """Request a certificate for a completed project."""
    project = get_object_or_404(Project, id=project_id)

    can_request, message = CertificateService.can_request_certificate(request.user, project)

    if not can_request:
        return Response(
            {"detail": message},
            status=status.HTTP_400_BAD_REQUEST
        )

    certificate = CertificateService.create_certificate(request.user, project)

    return Response(
        {
            "detail": "Certificate requested successfully.",
            "certificate_id": str(certificate.no)
        },
        status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def certificate_available(request, project_id):
    """Check if a certificate is available for request."""
    project = get_object_or_404(Project, id=project_id)

    available, message = CertificateService.is_certificate_available(request.user, project)

    response_status = status.HTTP_200_OK if available else status.HTTP_400_BAD_REQUEST

    return Response(
        {"available": available, "detail": message},
        status=response_status
    )


class ProjectSeedUploadView(APIView):
    """API view for uploading project seed data."""

    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        """Handle project seed upload."""
        logger.info(
            f"Received project seed upload request from user id: {request.user.id}, "
            f"user name: {request.user.first_name} {request.user.last_name}"
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
            return Response(
                {'error': f'An unexpected error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = {
            'id': project.id,
            'name': project.name,
            'slug': project.slug,
            'message': 'Project created successfully.',
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
