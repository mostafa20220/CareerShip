from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from projects.models.projects import Project, UserProject
from projects.serializers import ProjectSerializer
from utils.pagination import StandardPagination
from django.shortcuts import get_object_or_404
from certificates.models import Certificate
import uuid


@api_view(["GET"])
def list_projects(request):
    projects = Project.objects.all()

    # Filtering by difficulty_level and category (by name)
    difficulty_level = request.query_params.get("difficulty_level")
    category = request.query_params.get("category")
    if difficulty_level:
        projects = projects.filter(difficulty_level__name=difficulty_level)
    if category:
        projects = projects.filter(category__name=category)

    paginator = StandardPagination()
    paginated_projects = paginator.paginate_queryset(projects, request)

    data = ProjectSerializer(paginated_projects, many=True).data
    paginated_response = paginator.get_paginated_response(data)
    paginated_response.status_code = status.HTTP_200_OK

    return paginated_response


@api_view(["GET"])
def get_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    data = ProjectSerializer(project).data
    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_certificate(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    user_project = UserProject.objects.filter(
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
    user_project = UserProject.objects.filter(
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
