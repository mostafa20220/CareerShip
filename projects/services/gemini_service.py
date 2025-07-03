import json
import google.generativeai as genai
from django.conf import settings

from utils.logging_utils import get_logger

logger = get_logger(__name__)


class GeminiService:
    def __init__(self):
        """
        Initialize the Gemini service with API key and model configuration.
        """
        # Configure the API key
        genai.configure(api_key=settings.GEMINI_API_KEY)

        # Set up generation configuration
        generation_config = genai.GenerationConfig(
            temperature=0.9,
            top_p=1,
            top_k=1,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )

        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=generation_config
        )

    def generate_project_from_conversation(self, conversation_history):
        """
        Generate project JSON from conversation history.

        Args:
            conversation_history: List of message dictionaries with 'role' and 'parts' keys

        Returns:
            dict: Parsed JSON response from Gemini

        Raises:
            ValueError: If the response cannot be parsed as JSON
        """
        try:
            # Convert conversation history to the format expected by Gemini
            formatted_messages = []
            for message in conversation_history:
                formatted_messages.append({
                    "role": message["role"],
                    "parts": [{"text": part} for part in message["parts"]]
                })

            # Generate content using the conversation
            response = self.model.generate_content(formatted_messages)

            # Parse the JSON response
            return json.loads(response.text)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from Gemini: {e}")
            logger.error(f"Raw response: {response.text}")
            raise ValueError("AI response was not valid JSON")

        except Exception as e:
            logger.error(f"Error generating content with Gemini: {e}")
            raise ValueError(f"Failed to generate project: {str(e)}")
