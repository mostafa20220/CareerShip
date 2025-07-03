# projects/tasks.py

from celery import shared_task
from django.core.files.base import ContentFile

from projects.Services.screenshot_service import ScreenshotService, FeedbackService
from projects.models.projects import TeamProject, ScreenshotComparison
from projects.models.submission import Submission, FAILED
from projects.models.tasks_endpoints import Task
from utils.logging_utils import get_logger
import asyncio

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


@shared_task
def process_screenshot_comparison(team_project_id: int, task_id=None):
    """Async task to capture screenshot and compare with reference images"""
    try:
        team_project = TeamProject.objects.get(id=team_project_id)

        if not team_project.deployment_url:
            logger.error(f"No deployment URL for team project {team_project_id}")
            return

        if task_id:
            task = Task.objects.get(id=task_id)
        else:
            # Get the latest task for the project
            task = team_project.project.tasks.order_by('-order').first()

        if not task:
            logger.error(f"No task found for team project {team_project_id}")
            return

        reference_images = task.reference_images.all()

        if not reference_images.exists():
            logger.warning(f"No reference images found for task {task.id}")
            return

        screenshot_service = ScreenshotService()

        for ref_image in reference_images:
            try:
                # Capture screenshot
                screenshot_bytes = asyncio.run(
                    screenshot_service.capture_screenshot(
                        team_project.deployment_url,
                        ref_image.viewport_width,
                        ref_image.viewport_height
                    )
                )

                # Compare with reference image using PIL-only method
                try:
                    comparison_result = screenshot_service.compare_images(
                        ref_image.image.path,
                        screenshot_bytes
                    )
                except Exception as e:
                    logger.warning(f"SSIM comparison failed, falling back to PIL-only: {str(e)}")
                    comparison_result = screenshot_service.compare_images_pil_only(
                        ref_image.image.path,
                        screenshot_bytes
                    )

                # Generate detailed feedback
                feedback_text = FeedbackService.generate_detailed_feedback(comparison_result)

                # Create comparison record
                similarity_score = comparison_result.get('similarity_score') or comparison_result.get('pil_similarity',
                                                                                                      0)

                comparison = ScreenshotComparison.objects.create(
                    team_project=team_project,
                    reference_image=ref_image,
                    similarity_score=similarity_score,
                    feedback_text=feedback_text,
                    status='SUCCESS'
                )

                # Save screenshot
                screenshot_file = ContentFile(screenshot_bytes, name=f'screenshot_{team_project.id}_{ref_image.id}.png')
                comparison.screenshot.save(screenshot_file.name, screenshot_file)

                logger.info(f"Successfully processed screenshot comparison for team project {team_project_id}")

            except Exception as e:
                logger.error(f"Error processing screenshot for reference image {ref_image.id}: {str(e)}")
                ScreenshotComparison.objects.create(
                    team_project=team_project,
                    reference_image=ref_image,
                    status='ERROR',
                    feedback_text=f"Error processing screenshot: {str(e)}"
                )

    except Exception as e:
        logger.error(f"Error in process_screenshot_comparison task: {str(e)}")
