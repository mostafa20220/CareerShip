from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from CareerShip.permissions import IsStudent
from projects.models.submission import Submission
from projects.models.tasks_endpoints import Task
from projects.serializers import SubmissionDetailsSerializer, ListProjectSubmissionsSerializer
from projects.services import run_task_tests


class SubmissionViewSet(ModelViewSet):
    permission_classes = [IsStudent]
    http_method_names = ['get', 'post', 'head']

    def get_queryset(self):
        user = self.request.user
        filters = {"user": user, "project_id": self.kwargs.get("project_id")}

        if "task_id" in self.kwargs:
            filters["task_id"] = self.kwargs["task_id"]

        return Submission.objects.filter(**filters)

    def get_serializer_class(self):
        if self.action == 'list':
            return ListProjectSubmissionsSerializer
        return SubmissionDetailsSerializer

    def create(self, request, *args, **kwargs):
        
        task = get_object_or_404(Task,id=kwargs.get("task_id"))
        deployment_url = request.data.get("deployment_url")

        if not deployment_url:
            return Response({"error": "Deployment URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        submission = Submission.objects.create(
            task=task,
            user=request.user,
            deployment_url=deployment_url,
            status="pending"
        )

        run_task_tests.delay(task.id, deployment_url, submission.id)

        return Response({"message": "Task submission received and is being processed."}, status=status.HTTP_202_ACCEPTED)

