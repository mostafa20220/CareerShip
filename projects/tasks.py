# projects/tasks.py

from celery import shared_task
from projects.models.submission import Submission, FAILED
from utils.logging_utils import get_logger

# Set up logger
logger = get_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_submission_tests(self, submission_id: int):
    """
    Celery task to run tests for a submission.
    It uses SubmissionTestRunner to encapsulate the logic.
    """
    from projects.services import SubmissionTestRunnerService , ConsoleSubmissionTestRunnerService
    try:
        submission = Submission.objects.get(id=submission_id)
        if submission.project.category.name == "Console":
            print("Console Project")
            runner = ConsoleSubmissionTestRunnerService(submission_id)
        else:
            runner = SubmissionTestRunnerService(submission_id)
        return runner.run()
    except Submission.DoesNotExist:
        logger.warning(f"Submission with id {submission_id} does not exist.")
    except Exception as e:
        logger.error(f"An unexpected error occurred for submission_id {submission_id}: {e}")
        try:
            submission = Submission.objects.get(id=submission_id)
            submission.status = FAILED
            submission.fail_message = "Internal Server Error"
            submission.save()
        except Submission.DoesNotExist:
            logger.warning(f"Submission with id {submission_id} does not exist for error update.")
        raise self.retry(exc=e)


@shared_task
def requeue_stuck_submissions():
    """
    Finds submissions that have been in the pending state for too long and re-queues them.
    """
    stuck_submissions = Submission.get_stuck_submissions()
    for submission in stuck_submissions:
        logger.info(f"Re-queueing submission {submission.id} which is stuck in pending state.")
        run_submission_tests.delay(submission.id)
