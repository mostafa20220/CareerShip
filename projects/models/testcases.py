from django.db import models
from rest_framework.fields import empty

from projects.models.tasks_endpoints import Task, Endpoint


class TestType(models.TextChoices):
    API_REQUEST = 'API_REQUEST', 'API Request & Response'
    JSON_VALIDATION = 'JSON_VALIDATION', 'JSON Structure Validation'
    CONSOLE_APPLICATION = 'CONSOLE_APPLICATION', 'Console Application'


class TestCase(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='test_cases', db_index=True
    )
    name = models.CharField(
        max_length=255, help_text="A human-readable name for the test, e.g., 'Test for 404 on non-existent task'."
    )
    description = models.TextField(
        blank=True, help_text="Optional: A more detailed explanation of what this test verifies."
    )
    test_type = models.CharField(
        max_length=50, choices=TestType.choices, default=TestType.API_REQUEST
    )
    points = models.PositiveSmallIntegerField(
        default=5, help_text="How many points this test is worth."
    )
    stop_on_failure = models.BooleanField(
        default=False, help_text="If true, the test run will stop if this case fails."
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Execution order of the test (e.g., 0, 1, 2...). Tests run in ascending order."
    )

    ## command_args maybe useful for cli apps
    command_args = models.JSONField(default=list,blank=True,null=True, help_text="Command line arguments")
    input_data = models.TextField(blank=True, help_text="Input data for console application")
    expected_output = models.TextField(blank=True, help_text="Expected console output")

    class Meta:
        # --- AND ADD THIS META OPTION ---
        ordering = ['order'] # Default ordering for all queries
        constraints = [
            models.UniqueConstraint(fields=['task', 'order'], name='unique_order_per_task')
        ]


    def __str__(self):
        return f"{self.order}: {self.name}"


class ApiTestCase(models.Model):
    test_case = models.OneToOneField(
        TestCase, on_delete=models.CASCADE, primary_key=True, related_name='api_details'
    )
    endpoint = models.ForeignKey(Endpoint, on_delete=models.CASCADE)

    path_params = models.JSONField(
        blank=True, null=True,
        help_text="Parameters to substitute into the endpoint path, e.g., {'id': 99999} or {'id': '{{context.id}}'}"
    )

    # Define the request to be sent
    request_payload = models.JSONField(
        blank=True, null=True, help_text="JSON body to send with the request (for POST, PUT)."
    )
    request_headers = models.JSONField(
        blank=True, null=True, help_text="JSON object of headers to send."
    )

    expected_status_code = models.PositiveSmallIntegerField(
        help_text="The expected HTTP status code, e.g., 200, 201, 404."
    )
    expected_response_schema = models.JSONField(
        blank=True, null=True, help_text="Optional: A JSON schema to validate the response structure against."
    )


    def __str__(self):
        return f"API Test for: {self.test_case.name}"
