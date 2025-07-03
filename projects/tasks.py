# projects/tasks.py

from celery import shared_task
from projects.models.submission import Submission, FAILED
from utils.logging_utils import get_logger
import json
from django.core.exceptions import ObjectDoesNotExist
from CareerShip.settings import BASE_DIR
from projects.models import Project
from projects.models.drafts import ProjectDraft, DraftStatus
from projects.services.gemini_service import GeminiService
from projects.services.project_generator import ProjectGenerator

# Set up logger
logger = get_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def generate_project_draft_task(self, draft_id: int):
    """
    Celery task to generate or refine a project draft.
    This task orchestrates the project generation by using the ProjectGenerator service.
    """
    try:
        draft = ProjectDraft.objects.select_related('category', 'difficulty_level').get(id=draft_id)
    except ObjectDoesNotExist:
        logger.warning(f"ProjectDraft with id {draft_id} does not exist. Task cannot proceed.")
        return

    try:
        # Instantiate the generator service with the draft
        generator = ProjectGenerator(draft=draft)
        # Run the generation process (which updates the draft instance in memory)
        generator.generate()
        # Save the updated draft to the database
        draft.save()

        logger.info(f"Successfully generated project draft for id: {draft_id}")

    except Exception as e:
        logger.error(f"Error in generate_project_draft_task for draft_id {draft_id}: {e}")
        draft.status = DraftStatus.ARCHIVED
        draft.save()
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_submission_tests(self, submission_id: int):
    """
    Celery task to run tests for a submission.
    It uses SubmissionTestRunner to encapsulate the logic.
    """
    from projects.services.submissions_services import SubmissionTestRunnerService
    try:
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
