import json
from django.conf import settings
from projects.models import Project
from projects.models.drafts import ProjectDraft, DraftStatus
from .gemini_service import GeminiService


class AIPoweredProjectGenerator:
    """
    Encapsulates the logic for generating a project draft using an AI service.
    """

    def __init__(self, draft: ProjectDraft):
        self.draft = draft
        self.gemini_service = GeminiService()

    def generate(self):
        """
        Generates the project content by building a system prompt and passing it
        along with the conversation history to the AI service.
        """
        # 1. Build the system prompt that contains all the rules and context.
        system_prompt = self._build_system_prompt()

        # 2. Generate the project using the conversation history and the system prompt.
        # The gemini_service is stateless and initialized in __init__.
        generated_json = self.gemini_service.generate_project_from_conversation(
            conversation_history=self.draft.conversation_history,
            system_instruction=system_prompt
        )

        # 3. Update the draft instance with the new JSON.
        self._update_draft_instance(generated_json)

    def _update_draft_instance(self, generated_json: dict):
        """
        Updates the draft object in memory with the newly generated content.
        Note: This does not save the object to the database.
        """
        self.draft.latest_project_json = generated_json
        self.draft.conversation_history.append({"role": "model", "parts": [json.dumps(generated_json)]})
        self.draft.status = DraftStatus.PENDING_REVIEW

    def _build_system_prompt(self) -> str:
        """
        Constructs the detailed system prompt for the AI by assembling various parts.
        This prompt sets the context, rules, and expected output format, but does
        not include the user's specific request, which is part of the conversation.
        """
        prompt_parts = [
            "You are a senior software engineer and curriculum developer designing a project for a learning platform.",
            "Your response MUST be a single, valid JSON object and nothing else, strictly adhering to the schema of the provided example.",
            "You must create a comprehensive set of test cases that cover not only the 'happy path' but also critical edge cases like invalid input, authentication failures, and authorization rules.",
            f"To avoid creating duplicates, here is a list of projects that already exist on the platform: {self._get_existing_projects_json()}.",
            f"The project MUST be in the '{self.draft.category.name}' category."
        ]

        if self.draft.difficulty_level:
            prompt_parts.append(f"The project's difficulty level MUST be '{self.draft.difficulty_level.name}'.")

        prompt_parts.append(f"The JSON object must strictly adhere to the schema of the following example: {self._get_golden_example_json()}.")
        prompt_parts.append("Now, generate a new and unique project based on the user request(s) in the conversation.")

        return " ".join(prompt_parts)

    def _get_existing_projects_json(self) -> str:
        """
        Fetches existing project details as a JSON string.
        """
        projects = list(Project.objects.values('name', 'description'))
        return json.dumps(projects)

    def _get_golden_example_json(self) -> str:
        """
        Loads the golden example from the JSON file and returns it as a string.
        """
        file_path = settings.BASE_DIR / 'URL_Shortener_API_Project_Seed.json'
        with open(file_path, 'r') as f:
            return json.dumps(json.load(f))
