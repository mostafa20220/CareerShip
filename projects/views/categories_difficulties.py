from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from projects.models.categories_difficulties import Category, DifficultyLevel
from projects.serializers import CategorySerializer, DifficultyLevelSerializer


@api_view(["GET"])
def list_categories(request):
    categories = Category.objects.all()
    data = CategorySerializer(categories, many=True).data

    return Response(data, status=status.HTTP_200_OK)


class ListDifficultiesView(ListAPIView):
    queryset = DifficultyLevel.objects.all()
    serializer_class = DifficultyLevelSerializer