from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from .logging_utils import get_logger

logger = get_logger(__name__)

def global_exception_handler(exc, context):
    # Let DRF handle its own exceptions first
    response = exception_handler(exc, context)

    if response is None:
        # Log the full traceback for debugging
        logger.error("Unhandled exception caught by global exception handler", exc_info=True)

        # Return a generic response for unexpected errors
        response = Response(
            {"error": "Something went wrong on our end. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response