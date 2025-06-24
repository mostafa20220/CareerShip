# projects/tasks.py

import requests
import jsonschema
from typing import List, Dict, Any
import re
import logging

from celery import shared_task
from django.utils import timezone

from projects.models.submission import Submission
from projects.models.testcases import TestCase, TestType

# Set up logger
logger = logging.getLogger('django')


def validate_json_schema(instance: Dict[str, Any], schema: Dict[str, Any]) -> (bool, str):
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

@shared_task
def run_submission_tests(submission_id: int):
    # ... (initial setup code is the same) ...
    try:
        submission = Submission.objects.select_related('task').get(pk=submission_id)
    except Submission.DoesNotExist:
        return f"Submission with ID {submission_id} not found. Halting task."

    base_url = submission.deployment_url.rstrip('/')
    test_cases = TestCase.objects.filter(task=submission.task).order_by('order').select_related('api_details__endpoint')

    results_log = []
    total_points_earned = 0
    total_possible_points = 0
    test_run_failed = False
    test_context = {}

    for i, test_case in enumerate(test_cases):
        passed = False
        feedback = "This test case was not run."
        total_possible_points += test_case.points

        if test_case.test_type == TestType.API_REQUEST:
            try:
                passed, feedback, test_context = _run_api_test(test_case, base_url, test_context)
            except Exception as e:
                passed = False
                feedback = f"A critical error occurred while running the API test: {str(e)}"
        else:
            feedback = f"Test type '{test_case.test_type}' is not supported."

        if passed:
            total_points_earned += test_case.points

        results_log.append({
            "test_case_id": test_case.id,
            "name": test_case.name,
            "passed": passed,
            "points_earned": test_case.points if passed else 0,
            "feedback": feedback,
        })

        if not passed:
            test_run_failed = True
            if test_case.stop_on_failure:
                for skipped_test in test_cases[i+1:]:
                    results_log.append({
                        "test_case_id": skipped_test.id,
                        "name": skipped_test.name,
                        "passed": False,
                        "points_earned": 0,
                        "feedback": "Skipped due to previous critical failure.",
                    })
                break

    # ... (Finalize Submission code is the same) ...
    submission.execution_logs = results_log
    submission.passed_tests = len([res for res in results_log if res['passed']])
    submission.passed_percentage = (total_points_earned / total_possible_points) * 100 if total_possible_points > 0 else 0
    submission.status = 'failed' if test_run_failed else 'passed'
    submission.completed_at = timezone.now()
    submission.save()

    return f"Finished processing submission {submission_id}. Status: {submission.status}"


def _run_api_test(test_case: TestCase, base_url: str, context: dict) -> (bool, str, dict):
    """
    Private helper with updated logic to handle explicit path_params.
    """
    api_details = test_case.api_details
    path = api_details.endpoint.path

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
                    return False, f"Test failed: Context variable '{context_key}' not found for path parameter.", context
            else:
                return False, f"Test failed: Invalid context variable format '{value}'.", context
        else:
            # It's a literal value, just substitute it
            path = path.replace(placeholder, str(value))

    full_url = f"{base_url}{path}"
    method = api_details.endpoint.method

    logger.info(f"Running API test for URL: {full_url}")
    logger.info(f"Using method: {method}")
    logger.info(f"Request Headers: {api_details.request_headers}")
    logger.info(f"Request Payload: {api_details.request_payload}")

    try:
        response = requests.request(
            method=method,
            url=full_url,
            headers=api_details.request_headers,
            json=api_details.request_payload,
            timeout=10
        )
        actual_status_code = response.status_code
    except requests.exceptions.RequestException as e:
        return False, f"Failed to connect to API at {full_url}. Error: {e}", context

    if actual_status_code != api_details.expected_status_code:
        feedback = f"Status Code Mismatch. Expected {api_details.expected_status_code}, but got {actual_status_code}."
        return False, feedback, context

    try:
        response_json = response.json() if response.content else None
    except ValueError:
        return False, "The API response was not valid JSON, although it was expected to be.", context

    is_valid, schema_feedback = validate_json_schema(
        instance=response_json,
        schema=api_details.expected_response_schema
    )

    if not is_valid:
        return False, schema_feedback, context

    if method == 'POST' and actual_status_code == 201 and response_json and 'id' in response_json:
        context['id'] = response_json['id']

    return True, "Test passed: Status code and response schema are correct.", context
