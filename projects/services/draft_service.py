from .project_seed_service import ProjectSeederService, ProjectCreationError
from ..models import ProjectDraft, DraftStatus
from ..tasks import generate_project_draft_task
from django.core.exceptions import ObjectDoesNotExist


class DraftService:
    def __init__(self, user):
        self.user = user

    def create_draft(self, prompt: str, category_id: int, is_public: bool, difficulty_level_id: int = None, name: str = None) -> ProjectDraft:
        """
        Creates a new project draft and triggers the initial generation task.
        """
        # The conversation history starts with the initial system prompt and the user's first message.
        # The actual system prompt will be constructed in the Celery task.
        initial_conversation = [{"role": "user", "parts": [prompt]}]

        draft = ProjectDraft.objects.create(
            user=self.user,
            category_id=category_id,
            difficulty_level_id=difficulty_level_id,
            name=name,
            is_public=is_public,
            conversation_history=initial_conversation,
            status=DraftStatus.GENERATING

        )

        # Trigger the asynchronous task to generate the project content.
        generate_project_draft_task.delay(draft.id)

        return draft

    def refine_draft(self, draft_id: int, prompt: str) -> ProjectDraft:
        """
        Adds a new user message to the conversation and triggers the generation task again.
        """
        try:
            draft = ProjectDraft.objects.get(id=draft_id, user=self.user)
        except ObjectDoesNotExist:
            raise ValueError("Draft not found or you don't have permission to access it.")

        # Append the new user instruction to the conversation history.
        draft.conversation_history.append({"role": "user", "parts": [prompt]})
        draft.status = DraftStatus.GENERATING
        draft.save()

        # Trigger the asynchronous task to refine the project content.
        generate_project_draft_task.delay(draft.id)

        return draft

    def finalize_project_from_draft(self, draft_id: int, is_public: bool = True) -> ProjectDraft:
        """
        Uses the latest generated JSON from a draft to create a permanent project.
        """
        try:
            draft = ProjectDraft.objects.get(id=draft_id, user=self.user)
        except ObjectDoesNotExist:
            raise ValueError("Draft not found or you don't have permission to access it.")

        if not draft.latest_project_json:
            raise ValueError("Cannot create a project. The draft has no generated content.")

        if draft.status != DraftStatus.PENDING_REVIEW:
            raise ValueError(f"Draft must be in '{DraftStatus.PENDING_REVIEW}' status to be finalized.")

        try:
            # Pass the is_public flag and user from the draft to the seeder service
            seeder_service = ProjectSeederService(draft.latest_project_json, is_public or draft.is_public, draft.user)
            project = seeder_service.create_project()

            # Mark the draft as completed.
            draft.status = DraftStatus.COMPLETED
            draft.save()

            return project
        except ProjectCreationError as e:
            # Re-raise the specific creation error to be handled by the caller.
            raise e

    def delete_draft(self, draft_id: int):
        """
        Deletes a project draft for the user.
        """
        try:
            draft = ProjectDraft.objects.get(id=draft_id, user=self.user)
            draft.delete()
        except ObjectDoesNotExist:
            raise ValueError("Draft not found or you don't have permission to access it.")
