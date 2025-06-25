# projects/tasks.py

from celery import shared_task
from django.utils import timezone

from projects.models.submission import Submission, FAILED
from projects.services import SubmissionTestRunnerService
from utils.logging_utils import get_logger

# Set up logger
logger = get_logger(__name__)


@shared_task
def run_submission_tests(submission_id: int):
    """
    Celery task to run tests for a submission.
    It uses SubmissionTestRunner to encapsulate the logic.
    """
    try:
        runner = SubmissionTestRunnerService(submission_id)
        return runner.run()
    except Submission.DoesNotExist:
        logger.error(f"Submission with ID {submission_id} not found. Halting task.")
        return f"Submission with ID {submission_id} not found. Halting task."
    except Exception as e:
        logger.critical(f"An unexpected error occurred while processing submission {submission_id}: {e}", exc_info=True)
        try:
            # Attempt to update submission to an 'error' state
            submission = Submission.objects.get(pk=submission_id)
            submission.status = FAILED
            submission.feedback = 'An unexpected server error occurred during testing. Please contact support.'
            submission.execution_logs = [{'error': str(e)}]
            submission.completed_at = timezone.now()
            submission.save()
        except Submission.DoesNotExist:
            logger.warning(f"Submission {submission_id} was deleted before it could be marked as failed.")
            pass  # The submission was already gone
        except Exception as inner_e:
            logger.error(f"Could not update submission {submission_id} to error state after a critical failure. Reason: {inner_e}", exc_info=True)

        return f"An unexpected error occurred for submission {submission_id}."
