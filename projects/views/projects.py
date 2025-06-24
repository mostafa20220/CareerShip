from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from projects.models.projects import Project
from projects.serializers import ProjectSerializer
from utils.pagination import StandardPagination
from django.shortcuts import get_object_or_404


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
