import json
import google.generativeai as genai
from django.conf import settings
from enum import Enum

from utils.logging_utils import get_logger

logger = get_logger(__name__)

class AI_MODELS(Enum):
    MODEL_2_5_FLASH = "gemini-2.5-flash"
    MODEL_2_5_PRO = "gemini-2.5-pro"


class GeminiService:
    def __init__(self):
        """
        Initializes the Gemini Service, configuring the API key.
        This service is stateless and can be used for various generation tasks.
        """
        self.model = None
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def generate_project_from_conversation(self, conversation_history: list, system_instruction: str):
        """
        Generates project JSON from a conversation history, guided by a system instruction.
        """
        generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        self.model = genai.GenerativeModel(
            model_name=AI_MODELS.MODEL_2_5_FLASH.value,
            generation_config=generation_config,
            system_instruction=system_instruction  # Pass system instruction here
        )

        response = self.model.generate_content(conversation_history)

        try:
            return json.loads(response.text)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Error decoding Gemini response: {e}")
            logger.error(f"Raw response text: {response.text}")
            raise ValueError("Failed to generate a valid project structure from the AI.")
