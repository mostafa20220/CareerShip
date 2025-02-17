from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from .models import *
from .serializers import CategorySerializer

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
