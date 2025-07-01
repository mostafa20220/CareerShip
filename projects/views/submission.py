from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from projects.models.submission import Submission
from projects.serializers import SubmissionDetailsSerializer, ListProjectSubmissionsSerializer, \
    CreateSubmissionSerializer, CreateConsoleSubmissionSerializer


class SubmissionViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head']

    def get_queryset(self):
        user = self.request.user
        project_id = self.kwargs.get("project_id")
        task_id = self.kwargs.get("task_id")

        # Filter submissions to those belonging to the user's teams
        queryset = Submission.objects.filter(
            team__in=user.teams.all(),
            project_id=project_id
        )

        if task_id:
            queryset = queryset.filter(task_id=task_id)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ListProjectSubmissionsSerializer
        if self.action == 'create':
            from projects.models.projects import Project
            project_id = self.kwargs.get("project_id")
            project = get_object_or_404(Project, pk=project_id)
            if project.category.name == 'Console':
                return CreateConsoleSubmissionSerializer
            else:
                return CreateSubmissionSerializer

        return SubmissionDetailsSerializer

    def create(self, request, *args, **kwargs):
        project_id = kwargs.get("project_id")
        task_id = kwargs.get("task_id")

        serializer = self.get_serializer(data=request.data, context={
            'request': request,
            'project_id': project_id,
            'task_id': task_id
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Task submission received and is being processed."}, status=status.HTTP_202_ACCEPTED)
