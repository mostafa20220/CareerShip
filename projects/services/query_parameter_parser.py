from typing import Dict, Any, Optional
from rest_framework.request import Request


class QueryParameterParser:
    """Service responsible for parsing and validating query parameters."""

    SUPPORTED_FILTERS = [
        'category',
        'difficulty_level',
        'is_premium',
        'is_public',
        'is_registered'
    ]

    @classmethod
    def extract_filters(cls, request: Request) -> Dict[str, Any]:
        """Extract filter parameters from request query params."""
        filters = {}

        for param_name in cls.SUPPORTED_FILTERS:
            param_value = request.query_params.get(param_name)
            if param_value is not None:
                filters[param_name] = param_value

        return filters

    @classmethod
    def validate_boolean_param(cls, value: str) -> Optional[bool]:
        """Validate and convert boolean parameter values."""
        if value is None:
            return None

        value_lower = value.lower()
        if value_lower == 'true':
            return True
        elif value_lower == 'false':
            return False

        return None
