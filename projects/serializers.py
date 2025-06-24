from rest_framework import serializers

from projects.models.categories_difficulties import Category, DifficultyLevel
from projects.models.projects import Project
from projects.models.submission import Submission
from projects.models.tasks_endpoints import Task, MethodType, Endpoint


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id", "name"]


class TaskSerializer(serializers.ModelSerializer):
    difficulty_level = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%d %b %Y")

    class Meta:
        model = Task
        fields = ["id", "name", "slug", "difficulty_level", "created_at"]

    def get_difficulty_level(self, obj):
        return obj.difficulty_level.name if obj.difficulty_level else None



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

class EndpointDetailsSerializer(serializers.ModelSerializer):
    task = serializers.StringRelatedField()

    class Meta:
        model = Endpoint
        fields = ["id", "task", "method", "path", "description"]


class TaskDetailsSerializer(serializers.ModelSerializer):
    difficulty_level = serializers.StringRelatedField()
    created_at = serializers.DateTimeField(format="%d %b %Y")
    endpoints = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "duration_in_days",
            "difficulty_level",
            "created_at",
            "endpoints"
        ]

    def get_endpoints(self, obj):
        endpoints = Endpoint.objects.filter(task=obj)
        return EndpointDetailsSerializer(endpoints, many=True).data

class ProjectDetailsSerializer(serializers.ModelSerializer):
    difficulty_level = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    created_at = serializers.DateTimeField(format="%d %b %Y")
    tasks = TaskDetailsSerializer(many=True)

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
        fields = ["id", "name"]


class SubmissionDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Submission
        fields = "__all__"

class CreateSubmissionSerializer(serializers.ModelSerializer):


    class Meta:
        model = Submission
        fields=[
            'user','project' ,'task', 'status', 'deployment_url',
        ]
        read_only_fields = [
            'id', 'user', 'status', 'passed_percentage',
            'execution_logs', 'feedback', 'created_at', 'completed_at'
        ]

    def validate_deployment_url(self, value):
        # Basic validation for the URL
        if not value.startswith('http://') and not value.startswith('https://'):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value


class ListTaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = "__all__"


class ListProjectSubmissionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Submission
        exclude = ["execution_logs", "feedback"]




class ApiTestCaseSeedSerializer(serializers.Serializer):
    endpoint_path = serializers.CharField(max_length=255)
    path_params = serializers.JSONField(required=False, allow_null=True)
    method = serializers.ChoiceField(choices=MethodType.choices)
    request_payload = serializers.JSONField(required=False, allow_null=True)
    request_headers = serializers.JSONField(required=False, allow_null=True)
    expected_status_code = serializers.IntegerField(min_value=100, max_value=599)
    expected_response_schema = serializers.JSONField(required=False, allow_null=True)


class TestCaseSeedSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    order = serializers.IntegerField(default=0, min_value=0)
    description = serializers.CharField(required=False, allow_blank=True)
    test_type = serializers.CharField(max_length=50) # Assuming validation against TestType choices happens in service
    points = serializers.IntegerField(min_value=0)
    stop_on_failure = serializers.BooleanField(default=False)
    api_details = ApiTestCaseSeedSerializer(required=False)

    def validate(self, data):
        if data.get('test_type') == 'API_REQUEST' and 'api_details' not in data:
            raise serializers.ValidationError("api_details are required for test_type 'API_REQUEST'")
        return data


class EndpointSeedSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=MethodType.choices)
    path = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)


class TaskSeedSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField()
    description = serializers.CharField()
    duration_in_days = serializers.IntegerField(min_value=1)
    prerequisites = serializers.ListField(child=serializers.CharField(), required=False, default=[])
    endpoints = EndpointSeedSerializer(many=True, required=False, default=[])
    test_cases = TestCaseSeedSerializer(many=True, required=False, default=[])


class ProjectSeedSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField()
    description = serializers.CharField()
    difficulty_level = serializers.CharField(max_length=255)
    category = serializers.CharField(max_length=255)
    is_premium = serializers.BooleanField(default=False)
    max_team_size = serializers.IntegerField(min_value=1)
    tasks = TaskSeedSerializer(many=True, required=True)

    def validate_tasks(self, value):
        if not value:
            raise serializers.ValidationError("A project must have at least one task.")
        return value
