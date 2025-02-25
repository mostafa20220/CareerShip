from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from .models import *
from .serializers import *
from utils.pagination import StandardPagination
from django.shortcuts import get_object_or_404

from teams.models import Team

import traceback


@api_view(["GET"])
def list_categories(request):
    categories = Category.objects.all()
    data = CategorySerializer(categories, many=True).data

    return Response(data, status=status.HTTP_200_OK)



@api_view(["GET"])
def list_projects(request):
    projects = Project.objects.all()

    paginator = StandardPagination()
    paginated_projects = paginator.paginate_queryset(projects, request)

    data = ProjectSerializer(paginated_projects, many=True).data
    paginated_response = paginator.get_paginated_response(data)
    paginated_response.status_code = status.HTTP_200_OK

    return paginated_response



@api_view(["GET"])
def get_project(request, pk):
    project = get_object_or_404(Project, id=pk)
    data = ProjectSerializer(project).data
    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
def submit_task(request):
    user = request.user
    task_id = request.data.get("task_id")
    team_id = request.data.get("team_id")
    deployment_url = request.data.get("deployment_url")
    github_url = request.data.get("github_url")

    task = Task.objects.get(id=task_id)
    team = Team.objects.get(id=team_id)
    submission = Submission.objects.create(user=user, task=task, team=team)

    if deployment_url:
        submission.deployment_url = deployment_url

    if github_url:
        submission.github_url = github_url

    submission.save()

    return Response(status=status.HTTP_200_OK)

