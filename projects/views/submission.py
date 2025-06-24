from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from projects.models.submission import Submission, PENDING
from projects.serializers import SubmissionDetailsSerializer, ListProjectSubmissionsSerializer, \
    CreateSubmissionSerializer
from projects.tasks import run_submission_tests

class SubmissionViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
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
        if self.action == 'create':
            return  CreateSubmissionSerializer
        return SubmissionDetailsSerializer

    def create(self, request, *args, **kwargs):

        task = kwargs.get("task_id")
        project = kwargs.get("project_id")
        deployment_url = request.data.get("deployment_url")

        # use the serializer to validate and create the submission
        # print("Creating submission with task:", task, "project:", project, "deployment_url:", deployment_url)

        serializer = self.get_serializer(data={
            "task": task,
            "project": project,
            "deployment_url": deployment_url
        })
        serializer.is_valid(raise_exception=True)
        submission = serializer.save(user=request.user, status=PENDING)

        run_submission_tests.delay(submission.id)
        return Response({"message": "Task submission received and is being processed."}, status=status.HTTP_202_ACCEPTED)
