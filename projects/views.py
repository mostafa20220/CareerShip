from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from .models import *
from .serializers import *

import traceback


@api_view(["GET"])
def list_categories(request):
    try:
        categories = Category.objects.all()
        data = CategorySerializer(categories, many=True).data

        return Response(data, status=status.HTTP_200_OK)
    except:
        print(traceback.format_exc())
        return Response(
            {"error": "Something went wrong."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def list_projects(request):
    try:
        projects = Project.objects.all()
        data = ProjectSerializer(projects, many=True).data

        return Response(data, status=status.HTTP_200_OK)
    except:
        print(traceback.format_exc())
        return Response(
            {"error": "Something went wrong."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def get_project(request, pk):
    try:
        project = Project.objects.get(id=pk)
        data = ProjectSerializer(project).data

        return Response(data, status=status.HTTP_200_OK)
    except:
        print(traceback.format_exc())
        return Response(
            {"error": "Something went wrong."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
