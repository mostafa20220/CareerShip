from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from celery import shared_task
import subprocess
import json

from django.db import transaction
from .models.projects import Project
from .models.tasks_endpoints import Task, Endpoint
from .models.categories_difficulties import Category, DifficultyLevel
from .models.prerequisites import Prerequisite, TaskPrerequisite
from projects.models.submission import Submission
from .models.testcases import TestCase, TestType, ApiTestCase


@shared_task
def run_task_tests(task_id, deployment_url, submission_id):
    task = get_object_or_404(Task, id=task_id)
    submission = get_object_or_404(Submission, id=submission_id)
    tests = task.tests  # List of test scripts stored as text

    passed_tests = 0
    total_tests = len(tests)
    failed_test_index = None
    execution_logs = []
    feedback_messages = []

    for index, test_code in enumerate(tests):
        test_script = f"""
import requests

base_url = "{deployment_url}"
{test_code}
"""

        try:
            result = subprocess.run(
                ["python3", "-c", test_script],
                capture_output=True,
                text=True,
                timeout=5  # Prevent infinite loops
            )

            execution_logs.append(result.stdout or result.stderr)

            if result.returncode == 0:
                passed_tests += 1
            else:
                failed_test_index = index
                feedback_messages.append(f"Test {index + 1} failed: {result.stderr.strip()}")
                break  # Stop at first failure

        except subprocess.TimeoutExpired:
            failed_test_index = index
            feedback_messages.append(f"Test {index + 1} failed: Execution timed out.")
            break

    passed_percentage = (passed_tests / total_tests) * 100
    submission.status = "passed" if passed_tests == total_tests else "failed"
    submission.passed_tests = passed_tests
    submission.failed_test_index = failed_test_index
    submission.passed_percentage = passed_percentage
    submission.execution_logs = json.dumps(execution_logs)
    submission.feedback = json.dumps(feedback_messages)
    submission.completed_at = now()
    submission.save()

    return submission.status



class ProjectCreationError(Exception):
    """Custom exception for project creation failures."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


class ProjectSeederService:
    def __init__(self, validated_data):
        self.data = validated_data

    @transaction.atomic
    def create_project(self) -> Project:
        """
        Creates a project and all its related objects from a validated data dictionary.
        Uses bulk_create for performance.
        """
        if Project.objects.filter(slug=self.data['slug']).exists():
            raise ProjectCreationError(f"Project with slug '{self.data['slug']}' already exists.", status_code=409)

        category = self._get_or_raise(Category, name=self.data['category'])
        difficulty = self._get_or_raise(DifficultyLevel, name=self.data['difficulty_level'])

        project = Project.objects.create(
            name=self.data['name'],
            slug=self.data['slug'],
            description=self.data['description'],
            category=category,
            difficulty_level=difficulty,
            is_premium=self.data['is_premium'],
            max_team_size=self.data['max_team_size']
        )

        tasks_data = self.data.get('tasks', [])
        if not tasks_data:
            return project  # Return early if no tasks

        # --- Bulk Creation Process ---
        task_map = self._bulk_create_tasks(project, tasks_data)
        self._bulk_create_task_prerequisites(task_map, tasks_data)
        endpoint_map = self._bulk_create_endpoints(task_map, tasks_data)
        self._bulk_create_test_cases(task_map, endpoint_map, tasks_data)

        return project

    def _bulk_create_tasks(self, project: Project, tasks_data: list) -> dict:
        tasks_to_create = [
            Task(
                project=project,
                name=data['name'],
                slug=data['slug'],
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
        for data in tasks_data:
            task = task_map.get(data['slug'])
            if task:
                for endpoint_data in data.get('endpoints', []):
                    endpoints_to_create.append(Endpoint(task=task, **endpoint_data))

        if not endpoints_to_create:
            return {}

        Endpoint.objects.bulk_create(endpoints_to_create)
        created_endpoints = Endpoint.objects.filter(task__in=task_map.values())
        return {(e.task_id, e.method, e.path): e for e in created_endpoints}

    def _bulk_create_test_cases(self, task_map: dict, endpoint_map: dict, tasks_data: list):
        test_cases_to_create = []
        api_details_data_list = []

        for data in tasks_data:
            task = task_map.get(data['slug'])
            if not task:
                continue

            for test_data in data.get('test_cases', []):
                print("test_data:", test_data)
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
                    api_details_data_list.append(test_data['api_details'])

        if not test_cases_to_create:
            return

        TestCase.objects.bulk_create(test_cases_to_create)

        # Map created test cases to the api_details data to prepare for ApiTestCase creation
        created_test_cases = TestCase.objects.filter(task__in=task_map.values()).select_related('task')
        test_case_map = {(tc.task.slug, tc.name): tc for tc in created_test_cases}

        api_test_cases_to_create = []
        for i, test_case_obj in enumerate(test_cases_to_create):
            if test_case_obj.test_type != TestType.API_REQUEST:
                continue

            test_case_key = (test_case_obj.task.slug, test_case_obj.name)
            created_test_case = test_case_map.get(test_case_key)
            api_details = api_details_data_list.pop(0)

            endpoint_key = (created_test_case.task_id, api_details['method'], api_details['endpoint_path'])
            endpoint = endpoint_map.get(endpoint_key)
            if not endpoint:
                raise ProjectCreationError(
                    f"Endpoint {endpoint_key[1]} {endpoint_key[2]} not defined for task {created_test_case.task.name}.")

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

#
#
#
# class ProjectCreationError(Exception):
#     """Custom exception for project creation failures."""
#
#     def __init__(self, message, status_code=400):
#         super().__init__(message)
#         self.status_code = status_code
#
#
# class ProjectSeederService:
#     def __init__(self, validated_data):
#         self.data = validated_data
#
#     @transaction.atomic
#     def create_project(self) -> Project:
#         if Project.objects.filter(slug=self.data['slug']).exists():
#             raise ProjectCreationError(f"Project with slug '{self.data['slug']}' already exists.", status_code=409)
#
#         category = self._get_or_raise(Category, name=self.data['category'])
#         difficulty = self._get_or_raise(DifficultyLevel, name=self.data['difficulty_level'])
#
#         project = Project.objects.create(
#             name=self.data['name'],
#             slug=self.data['slug'],
#             description=self.data['description'],
#             category=category,
#             difficulty_level=difficulty,
#             is_premium=self.data['is_premium'],
#             max_team_size=self.data['max_team_size']
#         )
#
#         for task_data in self.data['tasks']:
#             self._create_task_for_project(project, task_data)
#
#         return project
#
#     def _create_task_for_project(self, project: Project, task_data: dict):
#         task = Task.objects.create(
#             project=project,
#             name=task_data['name'],
#             slug=task_data['slug'],
#             description=task_data['description'],
#             duration_in_days=task_data['duration_in_days']
#         )
#
#         self._handle_prerequisites(task, task_data.get('prerequisites', []))
#
#         created_endpoints = {}
#         for endpoint_data in task_data.get('endpoints', []):
#             endpoint = self._create_endpoint_for_task(task, endpoint_data)
#             created_endpoints[(endpoint.method, endpoint.path)] = endpoint
#
#         for test_case_data in task_data.get('test_cases', []):
#             self._create_test_case_for_task(task, test_case_data, created_endpoints)
#
#     def _handle_prerequisites(self, task: Task, prerequisite_names: list):
#         for name in prerequisite_names:
#             prereq, _ = Prerequisite.objects.get_or_create(name=name)
#             TaskPrerequisite.objects.create(task=task, prerequisite=prereq)
#
#     def _create_endpoint_for_task(self, task: Task, endpoint_data: dict) -> Endpoint:
#         return Endpoint.objects.create(task=task, **endpoint_data)
#
#     def _create_test_case_for_task(self, task: Task, test_case_data: dict, endpoints_map: dict):
#         test_type_str = test_case_data['test_type']
#         if test_type_str not in TestType.values:
#             raise ProjectCreationError(f"Invalid test_type '{test_type_str}' provided.")
#
#         test_case = TestCase.objects.create(
#             task=task,
#             name=test_case_data['name'],
#             description=test_case_data.get('description', ''),
#             test_type=test_type_str,
#             points=test_case_data['points'],
#             stop_on_failure=test_case_data['stop_on_failure']
#         )
#
#         if test_type_str == TestType.API_REQUEST:
#             api_details_data = test_case_data.get('api_details')
#             self._create_api_test_case(test_case, api_details_data, endpoints_map)
#
#     def _create_api_test_case(self, test_case: TestCase, api_details_data: dict, endpoints_map: dict):
#         endpoint_key = (api_details_data['method'], api_details_data['endpoint_path'])
#         endpoint = endpoints_map.get(endpoint_key)
#
#         if not endpoint:
#             raise ProjectCreationError(f"Endpoint {endpoint_key[0]} {endpoint_key[1]} not defined for this task.")
#
#         ApiTestCase.objects.create(
#             test_case=test_case,
#             endpoint=endpoint,
#             request_payload=api_details_data.get('request_payload'),
#             request_headers=api_details_data.get('request_headers'),
#             expected_status_code=api_details_data['expected_status_code'],
#             expected_response_schema=api_details_data.get('expected_response_schema')
#         )
#
#     def _get_or_raise(self, model_class, **kwargs):
#         try:
#             return model_class.objects.get(**kwargs)
#         except model_class.DoesNotExist:
#             model_name = model_class.__name__
#             field, value = list(kwargs.items())[0]
#             raise ProjectCreationError(f"{model_name} with {field} '{value}' not found.")
