from rest_framework import serializers
from .models import Category, Project, Task


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class TaskSerializer(serializers.ModelSerializer):
    difficulty_level = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%d %b %Y")

    class Meta:
        model = Task
        fields = ["id", "name", "slug", "difficulty_level", "duration", "created_at"]

    def get_difficulty_level(self, obj):
        return obj.difficulty_level.name


class ProjectSerializer(serializers.ModelSerializer):
    difficulty_level = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%d %b %Y")
    tasks = TaskSerializer(many=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "slug",
            "is_premium",
            "created_at",
            "max_team_size",
            "difficulty_level",
            "category",
            "tasks",
        ]

    def get_difficulty_level(self, obj):
        return obj.difficulty_level.name

    def get_category(self, obj):
        return obj.category.name
