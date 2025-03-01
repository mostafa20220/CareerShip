from rest_framework import serializers

from projects.models.categories_difficulties import Category, DifficultyLevel
from projects.models.projects import Project
from projects.models.submission import Submission
from projects.models.tasks_endpoints import Task


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class TaskSerializer(serializers.ModelSerializer):
    difficulty_level = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%d %b %Y")

    class Meta:
        model = Task
        fields = ["id", "name", "slug", "difficulty_level", "created_at"]

    def get_difficulty_level(self, obj):
        return obj.difficulty_level.name


class ProjectSerializer(serializers.ModelSerializer):
    difficulty_level = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
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


class DifficultyLevelSerializer(serializers.ModelSerializer):

    class Meta:
        model = DifficultyLevel
        fields = ["id", "name", "description"]


class TaskDetailsSerializer(serializers.ModelSerializer):
    difficulty_level = serializers.StringRelatedField()
    created_at = serializers.DateTimeField(format="%d %b %Y")

    class Meta:
        model = Task
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "duration_in_days",
            "tests",
            "difficulty_level",
            "created_at",
        ]

class SubmissionDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Submission
        fields = "__all__"

class ListTaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = "__all__"


class ListProjectSubmissionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Submission
        fields = "__all__"
