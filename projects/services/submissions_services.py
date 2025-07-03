import re
from typing import Dict, Any, List

import jsonschema
import requests
from django.utils import timezone

from projects.models import Submission, PENDING, TestCase, TestType, Task, PASSED, TeamProject
from projects.tasks import run_submission_tests
from utils.logging_utils import get_logger

logger = get_logger(__name__)

class SubmissionService:
    def __init__(self, user, validated_data):
        self.user = user
        self.validated_data = validated_data

    def create(self):
        """
        Creates a submission based on validated data and triggers the test runner.
        """
        team_project = self.validated_data['team_project']
        deployment_url = self.validated_data['deployment_url']
        deployment_url_provided = self.validated_data['deployment_url_provided']

        submission = self._create_submission()

        if deployment_url_provided:
            self._update_team_project_deployment_url(team_project, deployment_url)

        run_submission_tests.delay(submission.id)
        return submission

    def _create_submission(self):
        """
        Creates and returns a new Submission instance.
        """
        return Submission.objects.create(
            project=self.validated_data['project'],
            task=self.validated_data['task'],
            team=self.validated_data['team'],
            user=self.user,
            deployment_url=self.validated_data['deployment_url'],
            github_url=self.validated_data.get('github_url'),
            status=PENDING
        )

    def _update_team_project_deployment_url(self, team_project, deployment_url):
        """
        Updates the team's project deployment URL if a new one was provided.
        """
        if team_project.deployment_url != deployment_url:
            team_project.deployment_url = deployment_url
            team_project.save(update_fields=['deployment_url'])


class SubmissionTestRunnerService:
    """
    Encapsulates the logic for running all tests for a given submission.
    """
    def __init__(self, submission_id: int):
        self.submission_id = submission_id
        self.submission = None
        self.base_url = ""
        self.project_tasks = []
        self.full_results_log = []
        self.is_submission_failed = False
        self.test_context = {}
        self.total_points_earned = 0
        self.total_possible_points = 0
        self.failed_task_name = ""

    def _validate_json_schema(self, instance: Dict[str, Any], schema: Dict[str, Any]) -> (bool, str):
        if not schema:
            return True, "No response schema was defined for this test case."
        try:
            jsonschema.validate(instance=instance, schema=schema)
            return True, "Response JSON matches the expected schema."
        except jsonschema.exceptions.ValidationError as e:
            error_message = f"Response JSON validation failed. Error in field '{'.'.join(e.path)}': {e.message}"
            return False, error_message
        except Exception as e:
            return False, f"An unexpected error occurred during schema validation: {str(e)}"

    def run(self):
        """Main method to run the entire test suite for the submission."""
        self._setup()
        self._execute_test_suite()
        self._finalize_submission()
        self._mark_project_as_finished()
        return self._get_status_message()

    def _setup(self):
        """Fetches submission and prepares for the test run."""
        self.submission = Submission.objects.select_related('task__project').get(pk=self.submission_id)
        self.base_url = self.submission.deployment_url.rstrip('/')
        submitted_task = self.submission.task
        self.project_tasks = submitted_task.project.tasks.filter(order__lte=submitted_task.order).order_by('order')
        # log the project tasks being tested
        logger.info(f"Running tests for project tasks: {[task.name for task in self.project_tasks]}")
        self.total_possible_points = sum(
            tc.points for task in self.project_tasks for tc in TestCase.objects.filter(task=task)
        )

    def _execute_test_suite(self):
        """Iterates through tasks and their test cases."""
        for task in self.project_tasks:
            self._run_tests_for_task(task)
            if self.is_submission_failed:
                self.failed_task_name = task.name
                break

    def _run_tests_for_task(self, task):
        """Runs all test cases for a single task."""
        test_cases = TestCase.objects.filter(task=task).order_by('order').select_related('api_details__endpoint')
        if not test_cases.exists():
            return

        for i, test_case in enumerate(test_cases):
            passed, feedback = self._run_single_test_case(test_case)
            self._log_result(task, test_case, passed, feedback)

            if not passed:
                self.is_submission_failed = True
                if test_case.stop_on_failure:
                    self._skip_remaining_tests_in_task(task, test_cases[i + 1:])
                    break

    def _run_single_test_case(self, test_case: TestCase) -> (bool, str):
        """Executes one test case and returns the result."""
        try:
            if test_case.test_type == TestType.API_REQUEST:
                passed, feedback, self.test_context = self._run_api_test(test_case, self.base_url, self.test_context)
                return passed, feedback
            return False, f"Test type '{test_case.test_type}' is not supported."
        except Exception as e:
            logger.error(f"Critical error on test case {test_case.id} for submission {self.submission_id}: {e}", exc_info=True)
            return False, f"A critical error occurred: {str(e)}"

    def _run_api_test(self, test_case: TestCase, base_url: str, context: dict) -> (bool, str, dict):
        """
        Private helper with updated logic to handle explicit path_params.
        """
        api_details = test_case.api_details
        path = api_details.endpoint.path

        logger.info(f"--- Running Test Case: {test_case.name} ---")
        logger.info(f"Initial context: {context}")

        # --- NEW: Smart Path Substitution Logic ---
        path_params = api_details.path_params or {}
        for key, value in path_params.items():
            placeholder = f"{{{key}}}"

            # Check if value is a context variable placeholder like '{{context.id}}'
            if isinstance(value, str) and '{{' in value and '}}' in value:
                match = re.search(r'\{\{context\.(\w+)\}\}', value)
                if match:
                    context_key = match.group(1)
                    if context_key in context:
                        path = path.replace(placeholder, str(context[context_key]))
                    else:
                        logger.error(f"Context variable '{{{{context.{context_key}}}}}' not found. Current context: {context}")
                        return False, f"Test failed: Context variable '{context_key}' not found for path parameter.", context
                else:
                    return False, f"Test failed: Invalid context variable format '{value}'.", context
            else:
                # It's a literal value, just substitute it
                path = path.replace(placeholder, str(value))

        full_url = f"{base_url}{path}"
        method = api_details.endpoint.method
        logger.info("-----------------------------starting API test----------------------------------")
        logger.info(f"Running API test for URL: {full_url}")
        logger.info(f"Using method: {method}")
        logger.info(f"Request Payload: {api_details.request_payload}")

        try:
            response = requests.request(
                method=method,
                url=full_url,
                headers=api_details.request_headers,
                json=api_details.request_payload,
                timeout=10,
                allow_redirects=False
            )
            actual_status_code = response.status_code
            #    logs response details
            logger.info(f"Received response with status code: {actual_status_code}")
            logger.info(f"Response Payload: {response.text}")
            logger.info("------------------------------- End of API test----------------------------------")
        except requests.exceptions.RequestException as e:
            return False, f"Failed to connect to API at {full_url}. Error: {e}", context

        # If status code is not what we expect, we fail and include the response body in the feedback.
        if actual_status_code != api_details.expected_status_code:
            if actual_status_code == 500:
                feedback = f"Status Code Mismatch. Expected {api_details.expected_status_code}, but got {actual_status_code}. Internal Server Error."
            else:
                feedback = (
                    f"Status Code Mismatch. Expected {api_details.expected_status_code}, but got {actual_status_code}. "
                    f"Response: {response.text}"
                )
            return False, feedback, context

        try:
            response_json = response.json() if response.content else None
        except ValueError:
            # If JSON is expected but not received, we fail and include the raw text.
            feedback = (
                "The API response was not valid JSON, although it was expected to be. "
                f"Received: {response.text}"
            )
            return False, feedback, context

        is_valid, schema_feedback = self._validate_json_schema(
            instance=response_json,
            schema=api_details.expected_response_schema
        )

        if not is_valid:
            # Append the actual response to the schema feedback.
            full_feedback = f"{schema_feedback} Received response: {response_json}"
            return False, full_feedback, context

        if method == 'POST' and actual_status_code == 201 and response_json:
            logger.info(f"Saving to context from POST response: {response_json}")
            for key, value in response_json.items():
                context[key] = value
            logger.info(f"Updated context: {context}")

        return True, "Test passed: Status code and response schema are correct.", context

    def _log_result(self, task: 'Task', test_case: TestCase, passed: bool, feedback: str):
        """Appends a result to the log."""
        points_earned = test_case.points if passed else 0
        if passed:
            self.total_points_earned += points_earned

        self.full_results_log.append({
            "task_id": task.id, "task_name": task.name,
            "test_case_id": test_case.id, "name": test_case.name,
            "passed": passed, "points_earned": points_earned,
            "feedback": feedback,
        })

    def _skip_remaining_tests_in_task(self, task: 'Task', skipped_tests: List[TestCase]):
        """Logs skipped test cases for a task."""
        for test_case in skipped_tests:
            self.full_results_log.append({
                "task_id": task.id, "task_name": task.name,
                "test_case_id": test_case.id, "name": test_case.name,
                "passed": False, "points_earned": 0,
                "feedback": "Skipped due to a critical failure in the same task.",
            })

    def _finalize_submission(self):
        """Updates and saves the submission model."""
        self.submission.execution_logs = self.full_results_log
        self.submission.passed_tests = len([res for res in self.full_results_log if res['passed']])
        self.submission.passed_percentage = (self.total_points_earned / self.total_possible_points) * 100 if self.total_possible_points > 0 else 0
        self.submission.status = 'failed' if self.is_submission_failed else 'passed'
        self.submission.completed_at = timezone.now()
        self.submission.save()

    def _get_status_message(self) -> str:
        """Generates a status message based on the submission results."""

        if self.submission.status == 'passed':
            return f"Submission {self.submission.id} passed successfully with {self.total_points_earned} points."
        else:
            return f"Submission {self.submission.id} failed. Last task: '{self.failed_task_name}'. Points earned: {self.total_points_earned} out of {self.total_possible_points}."

    def _mark_project_as_finished(self):
        """ Marks the project as finished if the submission passed, and it was the last task."""

        if self.submission.status == PASSED:
            submitted_task = self.submission.task
            project = submitted_task.project
            last_task = project.tasks.order_by('-order').first()

            if submitted_task == last_task:
                try:
                    team_project = TeamProject.objects.get(team=self.submission.team, project=project)
                    team_project.is_finished = True
                    team_project.finished_at = timezone.now()
                    team_project.save()
                    logger.info(f"Team {self.submission.team.id} has finished project {project.id}.")
                except TeamProject.DoesNotExist:
                    logger.error(f"TeamProject not found for team {self.submission.team.id} and project {project.id}.")
