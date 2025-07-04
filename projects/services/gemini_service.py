import json
import google.generativeai as genai
from django.conf import settings
from enum import Enum
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from utils.logging_utils import get_logger

logger = get_logger(__name__)

class AI_MODELS(Enum):
    MODEL_2_5_FLASH = "gemini-2.5-flash"
    MODEL_2_5_PRO = "gemini-2.5-pro"


class GeminiSafetyError(ValueError):
    """Custom exception for when the AI response is blocked for safety reasons."""

    pass


class GeminiResponseError(ValueError):
    """Custom exception for other non-retryable AI response errors (e.g., empty or invalid format)."""
    pass


class GeminiService:
    def __init__(self):
        """
        Initializes the Gemini Service, configuring the API key.
        This service is stateless and can be used for various generation tasks.
        """
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def generate_project_from_conversation(self, conversation_history: list, system_instruction: str):
        """
        Generates project JSON from a conversation history, guided by a system instruction.
        """
        generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            # "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        # Set safety settings to be less restrictive.
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        model = genai.GenerativeModel(
            model_name=AI_MODELS.MODEL_2_5_FLASH.value,
            generation_config=generation_config,
            system_instruction=system_instruction,
            safety_settings=safety_settings
        )

        response = model.generate_content(conversation_history)

        if not response.candidates:
            block_reason = response.prompt_feedback.block_reason
            logger.error(f"Prompt was blocked by Gemini API. Reason: {block_reason.name if block_reason else 'Unknown'}")
            raise GeminiSafetyError("The generation request was blocked by the AI's safety filters due to the prompt.")

        candidate = response.candidates[0]

        if candidate.finish_reason.name in ("SAFETY", "RECITATION"):
            logger.error(f"Gemini response was blocked. Finish reason: {candidate.finish_reason.name}")
            if candidate.safety_ratings:
                for rating in candidate.safety_ratings:
                    logger.error(f"  - Category: {rating.category.name}, Probability: {rating.probability.name}")
            raise GeminiSafetyError(f"The AI's response was blocked due to {candidate.finish_reason.name}.")

        if not candidate.content.parts:
            logger.error(f"Gemini response is empty. Finish reason: {candidate.finish_reason.name}")
            raise GeminiResponseError(f"The AI returned an empty response. Finish reason: {candidate.finish_reason.name}.")

        try:
            response_text = candidate.content.parts[0].text
            return json.loads(response_text)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Error decoding Gemini response: {e}")
            logger.error(f"Raw response text: {response_text}")
            raise GeminiResponseError("Failed to generate a valid project structure from the AI. The response was not valid JSON.")
