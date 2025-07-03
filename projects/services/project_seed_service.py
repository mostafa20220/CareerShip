from django.db import transaction, IntegrityError

from projects.models import Project, Category, DifficultyLevel, Task, Prerequisite, TaskPrerequisite, Endpoint, \
    TestCase, TestType, ApiTestCase
from utils.logging_utils import get_logger

logger = get_logger(__name__)

class ProjectCreationError(Exception):
    """Custom exception for project creation failures."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


class ProjectSeederService:
    def __init__(self, validated_data, is_public=True, user=None):
        self.data = validated_data
        self.is_public = is_public
        self.user = user

    @transaction.atomic
    def create_project(self) -> Project:
        """
        Creates a project and all its related objects from a validated data dictionary.
        Uses bulk_create for performance.
        """
        logger.info(f"Attempting to create project with slug: {self.data.get('slug')}")
        # if Project.objects.filter(slug=self.data['slug']).exists():
        #     raise ProjectCreationError(f"Project with slug '{self.data['slug']}' already exists.", status_code=409)

        category = self._get_or_raise(Category, name=self.data['category'])
        difficulty = self._get_or_raise(DifficultyLevel, name=self.data['difficulty_level'])

        try:
            project = Project.objects.create(
                name=self.data['name'],
                slug=self.data['slug'],
                description=self.data['description'],
                category=category,
                difficulty_level=difficulty,
                is_premium=self.data['is_premium'],
                max_team_size=self.data['max_team_size'],
                is_public=self.is_public,
                created_by=self.user
            )
        except IntegrityError:
            logger.warning(f"Race condition or duplicate slug prevented project creation for slug: {self.data.get('slug')}")
            raise ProjectCreationError(f"Project with slug '{self.data['slug']}' already exists.", status_code=409)

        tasks_data = self.data.get('tasks', [])
        if not tasks_data:
            return project  # Return early if no tasks

        # --- Bulk Creation Process ---
        task_map = self._bulk_create_tasks(project, tasks_data)
        self._bulk_create_task_prerequisites(task_map, tasks_data)
        endpoint_id_map = self._bulk_create_endpoints(task_map, tasks_data)
        self._bulk_create_test_cases(task_map, endpoint_id_map, tasks_data)

        return project

    def _bulk_create_tasks(self, project: Project, tasks_data: list) -> dict:
        tasks_to_create = [
            Task(
                project=project,
                name=data['name'],
                slug=data['slug'],
                order=data['order'],
                description=data['description'],
                duration_in_days=data['duration_in_days']
            ) for data in tasks_data
        ]
        Task.objects.bulk_create(tasks_to_create)

        # Fetch created tasks and map them by slug for relationship building
        created_tasks = Task.objects.filter(project=project)
        return {task.slug: task for task in created_tasks}

    def _bulk_create_task_prerequisites(self, task_map: dict, tasks_data: list):
        # Gather all unique prerequisite names
        all_prereq_names = set()
        for data in tasks_data:
            all_prereq_names.update(data.get('prerequisites', []))

        if not all_prereq_names:
            return

        # Find existing prerequisites and what needs to be created
        existing_prereqs = Prerequisite.objects.in_bulk(field_name='name', id_list=all_prereq_names)
        prereqs_to_create = [
            Prerequisite(name=name) for name in all_prereq_names if name not in existing_prereqs
        ]
        if prereqs_to_create:
            Prerequisite.objects.bulk_create(prereqs_to_create)

        # Create a complete map of prerequisite names to objects
        prereq_map = {p.name: p for p in Prerequisite.objects.filter(name__in=all_prereq_names)}

        # Prepare and bulk create the through-model objects
        task_prereqs_to_create = []
        for data in tasks_data:
            task = task_map.get(data['slug'])
            for prereq_name in data.get('prerequisites', []):
                prereq = prereq_map.get(prereq_name)
                if task and prereq:
                    task_prereqs_to_create.append(TaskPrerequisite(task=task, prerequisite=prereq))

        if task_prereqs_to_create:
            TaskPrerequisite.objects.bulk_create(task_prereqs_to_create)

    def _bulk_create_endpoints(self, task_map: dict, tasks_data: list) -> dict:
        endpoints_to_create = []
        endpoint_id_to_data = {}
        for data in tasks_data:
            task = task_map.get(data['slug'])
            if task:
                for endpoint_data in data.get('endpoints', []):
                    endpoint_data_copy = endpoint_data.copy()
                    endpoint_id = endpoint_data_copy.pop('id', None)

                    endpoints_to_create.append(Endpoint(task=task, **endpoint_data_copy))

                    if endpoint_id:
                        endpoint_id_to_data[endpoint_id] = {'task_id': task.id, 'method': endpoint_data_copy['method'], 'path': endpoint_data_copy['path']}

        if not endpoints_to_create:
            return {}

        Endpoint.objects.bulk_create(endpoints_to_create)
        created_endpoints = Endpoint.objects.filter(task__in=task_map.values())

        endpoint_map = {(e.task_id, e.method, e.path): e for e in created_endpoints}

        endpoint_id_map = {}
        for endpoint_id, data in endpoint_id_to_data.items():
            key = (data['task_id'], data['method'], data['path'])
            endpoint_obj = endpoint_map.get(key)
            if endpoint_obj:
                endpoint_id_map[endpoint_id] = endpoint_obj

        return endpoint_id_map

    def _bulk_create_test_cases(self, task_map: dict, endpoint_id_map: dict, tasks_data: list):
        test_cases_to_create = []
        api_details_data_list = []

        for data in tasks_data:
            task = task_map.get(data['slug'])
            if not task:
                continue

            for test_data in data.get('test_cases', []):
                test_case = TestCase(
                    task=task,
                    name=test_data['name'],
                    order=test_data.get('order'),
                    description=test_data.get('description', ''),
                    test_type=test_data['test_type'],
                    points=test_data['points'],
                    stop_on_failure=test_data['stop_on_failure'],
                )
                test_cases_to_create.append(test_case)

                if test_data.get('test_type') == TestType.API_REQUEST:
                    # Associate the test case with its api_details by order of appearance
                    api_details_data_list.append((test_case, test_data['api_details']))

        if not test_cases_to_create:
            return

        TestCase.objects.bulk_create(test_cases_to_create)

        # Map created test cases to the api_details data to prepare for ApiTestCase creation
        created_test_cases = TestCase.objects.filter(task__in=task_map.values()).select_related('task')
        test_case_map = {(tc.task.slug, tc.name): tc for tc in created_test_cases}

        api_test_cases_to_create = []
        for test_case_obj, api_details in api_details_data_list:
            test_case_key = (test_case_obj.task.slug, test_case_obj.name)
            created_test_case = test_case_map.get(test_case_key)

            endpoint_id = api_details.get('endpoint_id')
            if not endpoint_id:
                raise ProjectCreationError(f"Test case '{{created_test_case.name}}' is missing required 'endpoint_id' in 'api_details'.")

            endpoint = endpoint_id_map.get(endpoint_id)
            if not endpoint:
                raise ProjectCreationError(f"Endpoint with id '{{endpoint_id}}' not found for test case '{{created_test_case.name}}'.")

            api_test_cases_to_create.append(ApiTestCase(
                test_case=created_test_case,
                endpoint=endpoint,
                path_params=api_details.get('path_params', {}),
                request_payload=api_details.get('request_payload'),
                request_headers=api_details.get('request_headers'),
                expected_status_code=api_details['expected_status_code'],
                expected_response_schema=api_details.get('expected_response_schema')
            ))

        if api_test_cases_to_create:
            ApiTestCase.objects.bulk_create(api_test_cases_to_create)

    def _get_or_raise(self, model_class, **kwargs):
        try:
            return model_class.objects.get(**kwargs)
        except model_class.DoesNotExist:
            model_name = model_class.__name__
            field, value = list(kwargs.items())[0]
            raise ProjectCreationError(f"{model_name} with {field} '{value}' not found.")
