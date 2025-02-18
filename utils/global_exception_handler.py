from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import traceback

def global_exception_handler(exc, context):
    # Let DRF handle its own exceptions first
    response = exception_handler(exc, context)

    if response is None:
        # Log the full traceback for debugging (Optional)
        print(traceback.format_exc())

        # Return a generic response for unexpected errors
        response = Response(
            {"error": "Something went wrong on our end. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response