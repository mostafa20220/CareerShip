from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from celery import shared_task
import subprocess
import json

from projects.models.submission import Submission
from projects.models.tasks_endpoints import Task


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
