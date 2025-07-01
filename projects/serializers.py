from rest_framework import serializers

from projects.models.categories_difficulties import Category, DifficultyLevel
from projects.models.projects import Project, TeamProject
from projects.models.submission import Submission, PASSED
from projects.models.tasks_endpoints import Task, MethodType, Endpoint
from teams.models import Team
from .models.constants import PistonLanguages
from .services import SubmissionService, ConsoleSubmissionService


def validate_team(user, value):
    try:
        team = Team.objects.get(uuid=value)
    except Team.DoesNotExist:
        raise serializers.ValidationError("Team not found.")

    if user not in team.members.all():
        raise serializers.ValidationError("You are not a member of this team.")

    return team

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

class TeamProjectSerializer(serializers.ModelSerializer):
    project = ProjectSerializer()
    team = serializers.StringRelatedField()

    class Meta:
        model = TeamProject
        fields = "__all__"


class ProjectRegistrationSerializer(serializers.ModelSerializer):
    team = serializers.UUIDField()

    class Meta:
        model = TeamProject
        fields = ['id', 'project', 'team', 'deployment_url']
        read_only_fields = ['id']
        extra_kwargs = {
            'deployment_url': {'required': False, 'allow_blank': True}
        }

    def validate(self, data):
        team = data['team']
        project = data['project']
        user = self.context['request'].user

        team = validate_team(user,team)
        data['team'] = team

        if user != team.owner:
            raise serializers.ValidationError("You must be the team owner to register for a project.")

        if TeamProject.objects.filter(team=team, project=project).exists():
            raise serializers.ValidationError("This team is already registered for this project.")

        if project.is_premium and not team.owner.is_premium:
            raise serializers.ValidationError(
                "The team owner must be a premium user to register for a premium project."
            )

        if team.members.count() > project.max_team_size:
            raise serializers.ValidationError(
                f"The team size ({team.members.count()}) exceeds the maximum allowed size for this project ({project.max_team_size})."
            )

        return data

class DifficultyLevelSerializer(serializers.ModelSerializer):

    class Meta:
        model = DifficultyLevel
        fields = ["id", "name"]


class SubmissionDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Submission
        fields = "__all__"

class CreateSubmissionSerializer(serializers.ModelSerializer):
    team = serializers.UUIDField()

    class Meta:
        model = Submission
        fields = [
            'id', 'project', 'task', 'team', 'user', 'deployment_url', 'github_url', 'status'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'project', 'task'
        ]


    def validate_deployment_url(self, value):
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value

    def validate_github_url(self, value):
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value

    def validate(self, data):

        user = self.context['request'].user
        project_id = self.context['project_id']
        task_id = self.context['task_id']
        team = data.get('team')
        team = validate_team(user, team)
        data['team'] = team


        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            raise serializers.ValidationError("Project not found.")

        try:
            task = Task.objects.get(pk=task_id, project_id=project_id)
        except Task.DoesNotExist:
            raise serializers.ValidationError("Task not found in this project.")

        team = data['team']

        data['user'] = user
        data['project'] = project
        data['task'] = task

        try:
            team_project = TeamProject.objects.get(team=team, project=project)
        except TeamProject.DoesNotExist:
            raise serializers.ValidationError("Your team is not registered for this project.")

        if task.order > 0:
            previous_task_order = task.order - 1
            try:
                previous_task = Task.objects.get(project=project, order=previous_task_order)
                if not Submission.objects.filter(team=team, task=previous_task, status=PASSED).exists():
                    raise serializers.ValidationError(
                        f"Your team must pass the previous task '{previous_task.name}' before submitting this one."
                    )
            except Task.DoesNotExist:
                raise serializers.ValidationError("Could not find the previous task. Please contact support.")

        deployment_url = data.get('deployment_url')
        deployment_url_provided = bool(deployment_url)

        if not deployment_url:
            data['deployment_url'] = team_project.deployment_url

        if not data.get('deployment_url'):
            raise serializers.ValidationError({
                'deployment_url': "Deployment URL is required. "
                                  "Please provide it in the submission or register it with your project."
            })

        data['team_project'] = team_project
        data['deployment_url_provided'] = deployment_url_provided

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        service = SubmissionService(user=user, validated_data=validated_data)
        return service.create()


class CreateConsoleSubmissionSerializer(serializers.ModelSerializer):

    team = serializers.UUIDField()
    language = serializers.ChoiceField(
        choices=PistonLanguages.choices,
        required=True,
        error_messages={
            'required': 'Programming language is required for console submissions.',
            'invalid_choice': 'Invalid programming language. Please choose from the available options.'
        }
    )
    code = serializers.CharField(
        required=True,
        style={'base_template': 'textarea.html'},
        error_messages={
            'required': 'Code is required for console submissions.',
            'blank': 'Code cannot be empty.'
        }
    )

    class Meta:
        model = Submission
        fields = [
            'id',
            'project',
            'task',
            'team',
            'user',
            'github_url',
            'status',
            'language',
            'code'
        ]
        read_only_fields = [
            'id',
            'user',
            'status',
            'project',
            'task'
        ]


    def validate_code(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Code cannot be empty or contain only whitespace.")
        return value.strip()

    def validate(self, data):
        user = self.context['request'].user
        project_id = self.context['project_id']
        task_id = self.context['task_id']
        team = validate_team(user, data.get('team'))
        print(team)
        data['team'] = team

        # Validate project and task
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            raise serializers.ValidationError("Project not found.")

        try:
            task = Task.objects.get(pk=task_id, project_id=project_id)
        except Task.DoesNotExist:
            raise serializers.ValidationError("Task not found in this project.")



        # Validate team membership
        if user not in team.members.all():
            raise serializers.ValidationError("You are not a member of the team you are trying to submit for.")

        # Validate team project registration
        try:
            team_project = TeamProject.objects.get(team=team, project=project)
        except TeamProject.DoesNotExist:
            raise serializers.ValidationError("Your team is not registered for this project.")

        # Validate previous task completion
        if task.order > 0:
            previous_task_order = task.order - 1
            try:
                previous_task = Task.objects.get(project=project, order=previous_task_order)
                if not Submission.objects.filter(team=team, task=previous_task, status=PASSED).exists():
                    raise serializers.ValidationError(
                        f"Your team must pass the previous task '{previous_task.name}' before submitting this one."
                    )
            except Task.DoesNotExist:
                raise serializers.ValidationError("Could not find the previous task. Please contact support.")

        # Add validated objects to data
        data['user'] = user
        data['project'] = project
        data['task'] = task
        data['team_project'] = team_project

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        service = ConsoleSubmissionService(user=user, validated_data=validated_data)
        return service.create()




class ListTaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = "__all__"


class ListProjectSubmissionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Submission
        exclude = ["execution_logs", "feedback"]




class ApiTestCaseSeedSerializer(serializers.Serializer):
    endpoint_id = serializers.CharField(max_length=255)
    path_params = serializers.JSONField(required=False, allow_null=True)
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
    id = serializers.CharField(max_length=255)
    method = serializers.ChoiceField(choices=MethodType.choices)
    path = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)


class TaskSeedSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField()
    order = serializers.IntegerField(min_value=0)
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
