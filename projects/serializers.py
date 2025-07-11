from rest_framework import serializers

from projects.models.categories_difficulties import Category, DifficultyLevel
from projects.models.projects import Project, TeamProject
from projects.models.submission import Submission, PASSED
from projects.models.tasks_endpoints import Task, MethodType, Endpoint
from teams.models import Team
from teams.serializers import TeamSerializer
from .models import ProjectDraft, DraftStatus
from .services.submissions_services import SubmissionService
from .services.draft_service import DraftService

def validate_team(user, value):
    try:
        team = Team.objects.get(uuid=value)
    except Team.DoesNotExist:
        raise serializers.ValidationError("Team not found.")

    if user not in team.members.all():
        raise serializers.ValidationError("You are not a member of this team.")

    return team

class ProjectDraftCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True, source='category'
    )
    difficulty_level_id = serializers.PrimaryKeyRelatedField(
        queryset=DifficultyLevel.objects.all(), write_only=True, source='difficulty_level', required=False
    )
    is_public = serializers.BooleanField(default=False)

    class Meta:
        model = ProjectDraft
        fields = [
            'id', 'name','status', 'is_public', 'category', 'difficulty_level',
            'latest_project_json', 'conversation_history', 'created_at',
            'category_id', 'difficulty_level_id'
        ]
        read_only_fields = [
            'id', 'status', 'category', 'difficulty_level',
            'latest_project_json', 'conversation_history', 'created_at'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        draft_service = DraftService(user)

        # The source mapping handles category and difficulty_level assignment
        # We just need to pass the core data to the service.
        return draft_service.create_draft(
            category_id=validated_data['category'].id,
            difficulty_level_id=validated_data.get('difficulty_level').id if validated_data.get('difficulty_level') else None,
            is_public=validated_data['is_public'],
            name=validated_data.get('name'),
        )


# list drafts serializer
class ProjectDraftListSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    difficulty_level = serializers.StringRelatedField()

    class Meta:
        model = ProjectDraft
        fields = [
            'id', 'name','status', 'is_public', 'category', 'difficulty_level',
            'created_at'
        ]
        read_only_fields = ['id', 'status', 'category', 'difficulty_level', 'created_at']

# project draft details serializer
class ProjectDraftDetailsSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    difficulty_level = serializers.StringRelatedField()

    class Meta:
        model = ProjectDraft
        fields = [
            'id', 'name','status', 'is_public', 'category', 'difficulty_level',
            'latest_project_json', 'conversation_history', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'category', 'difficulty_level',
            'latest_project_json', 'conversation_history', 'created_at'
        ]

class ProjectDraftUpdateSerializer(serializers.ModelSerializer):
    is_public = serializers.BooleanField(default=False)
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)

    class Meta:
        model = ProjectDraft
        fields = ['name', 'is_public']
        read_only_fields = ['id', 'status', 'category', 'difficulty_level', 'latest_project_json', 'conversation_history', 'created_at']


# ceare a serializer for the refine request only
class ProjectDraftRefineSerializer(serializers.Serializer):
    prompt = serializers.CharField(min_length=10, required=True, write_only=True)

    class Meta:
        fields = ['prompt']
        read_only_fields = ['id','is_public' ,'status', 'category', 'difficulty_level', 'latest_project_json', 'conversation_history', 'created_at']

    def validate_prompt(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Prompt must be at least 10 characters long.")
        return value

    def validate(self, attrs):
        # check if it's in a valid state to refine
        if self.instance.status == DraftStatus.GENERATING:
            raise serializers.ValidationError("Draft is still being generated. Please wait until it's ready.")
        if self.instance.status == DraftStatus.COMPLETED:
            raise serializers.ValidationError("Draft has already been finalized.")
        if self.instance.status == DraftStatus.ARCHIVED:
            raise serializers.ValidationError("Draft has been archived and cannot be refined.")
        if self.instance.status != DraftStatus.PENDING_REVIEW:
            raise serializers.ValidationError("Draft must be in 'PENDING_REVIEW' status to be refined.")

        return attrs

    def update(self, instance, validated_data):
                user = self.context['request'].user
                prompt = validated_data['prompt']
                draft_service = DraftService(user)
                return draft_service.refine_draft(instance.id, prompt)

# generate project from draft serializer
class ProjectDraftFinalizeSerializer(serializers.Serializer):
    is_public = serializers.BooleanField(default=False, required=False)

    class Meta:
        fields = ['is_public']
        read_only_fields = ['id', 'status', 'category', 'difficulty_level', 'latest_project_json', 'conversation_history', 'created_at']

    def validate(self, attr):
        # check if it's in a valid state to finalize
        if self.instance.status == DraftStatus.GENERATING:
            raise serializers.ValidationError("Draft is still being generated. Please wait until it's ready.")
        if self.instance.status == DraftStatus.COMPLETED:
            raise serializers.ValidationError("Draft has already been finalized.")
        if self.instance.status == DraftStatus.ARCHIVED:
            raise serializers.ValidationError("Draft has been archived and cannot be finalized.")

        if not self.instance.latest_project_json:
            raise serializers.ValidationError("Draft has no generated content to finalize.")
        if self.instance.status != DraftStatus.PENDING_REVIEW:
            raise serializers.ValidationError("Draft must be in 'PENDING_REVIEW' status to be finalized.")

        return attr

    def update(self, instance, validated_data):
        user = self.context['request'].user
        draft_id = instance.id
        is_public = validated_data.get('is_public', instance.is_public)
        draft_service = DraftService(user)
        return draft_service.finalize_project_from_draft(draft_id, is_public)

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id", "name"]


class TaskSerializer(serializers.ModelSerializer):
    difficulty_level = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%d %b %Y")
    is_passed = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ["id", "name", "slug", "is_passed","difficulty_level", "created_at"]

    def get_difficulty_level(self, obj):
        return obj.difficulty_level.name if obj.difficulty_level else None

    def get_is_passed(self, obj):
        """Check if the current user has passed this task."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        from projects.models.submission import Submission, PASSED
        return Submission.objects.filter(
            team__members=request.user,
            task=obj,
            status=PASSED
        ).exists()



class ProjectSerializer(serializers.ModelSerializer):
    difficulty_level = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    created_at = serializers.DateTimeField(format="%d %b %Y")
    is_registered = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "slug",
            "is_premium",
            "is_public",
            "created_at",
            "max_team_size",
            "difficulty_level",
            "category",
            "is_registered",
            "created_by_name",
        ]

    def get_is_registered(self, obj):
        """Check if the current user is registered for this project through team membership."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        from projects.models.projects import TeamProject
        return TeamProject.objects.filter(
            team__members=request.user,
            project=obj
        ).exists()

    def get_created_by_name(self, obj):
        """Get the full name of the project creator."""
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return "Admins"

class EndpointDetailsSerializer(serializers.ModelSerializer):
    task = serializers.StringRelatedField()

    class Meta:
        model = Endpoint
        fields = ["id", "task", "method", "path", "description"]


class TaskDetailsSerializer(serializers.ModelSerializer):
    difficulty_level = serializers.StringRelatedField()
    created_at = serializers.DateTimeField(format="%d %b %Y")
    endpoints = serializers.SerializerMethodField()
    is_passed = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "order",
            "is_passed",
            "duration_in_days",
            "difficulty_level",
            "created_at",
            "endpoints"
        ]

    def get_endpoints(self, obj):
        endpoints = Endpoint.objects.filter(task=obj)
        return EndpointDetailsSerializer(endpoints, many=True).data

    def get_is_passed(self, obj):
        """Check if the current user has passed this task."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        from projects.models.submission import Submission, PASSED
        return Submission.objects.filter(
            team__members=request.user,
            task=obj,
            status=PASSED
        ).exists()

class ProjectDetailsSerializer(serializers.ModelSerializer):
    difficulty_level = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    created_at = serializers.DateTimeField(format="%d %b %Y")
    tasks = TaskSerializer(many=True)
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "slug",
            "is_premium",
            "is_public",
            "is_registered",
            "created_at",
            "max_team_size",
            "difficulty_level",
            "category",
            "tasks",
        ]

    def get_is_registered(self, obj):
        """Check if the current user is registered for this project through team membership."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        from projects.models.projects import TeamProject
        return TeamProject.objects.filter(
            team__members=request.user,
            project=obj
        ).exists()



class TeamProjectSerializer(serializers.ModelSerializer):
    project = ProjectSerializer()
    team = TeamSerializer()

    class Meta:
        model = TeamProject
        fields = ['id', 'project', 'team', 'is_finished', 'finished_at', 'created_at', 'deployment_url']


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

        if user not in team.members.all():
            raise serializers.ValidationError("You are not a member of the team you are trying to submit for.")

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


class ListTaskSerializer(serializers.ModelSerializer):
    is_passed = serializers.SerializerMethodField()
    class Meta:
        model = Task
        fields = "__all__"

    def get_is_passed(self, obj):
        """Check if the current user has passed this task."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        from projects.models.submission import Submission, PASSED
        return Submission.objects.filter(
            team__members=request.user,
            task=obj,
            status=PASSED
        ).exists()


class ListProjectSubmissionsSerializer(serializers.ModelSerializer):
    task = serializers.SerializerMethodField()
    user = serializers.StringRelatedField()
    team = serializers.StringRelatedField()

    class Meta:
        model = Submission
        exclude = ["execution_logs", "feedback","project"]

    def get_task(self, obj):
        """Return task id, order, name  and slug for the submission."""
        if obj.task:
            return {
                "id": obj.task.id,
                "name": obj.task.name,
                "order": obj.task.order,
            }
        return None




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
