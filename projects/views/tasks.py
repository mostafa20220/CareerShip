from rest_framework.generics import RetrieveAPIView, ListAPIView

from projects.models.tasks_endpoints import Task
from projects.serializers import TaskDetailsSerializer, ListTaskSerializer


class ListTasksView(ListAPIView):
    serializer_class = ListTaskSerializer

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return Task.objects.filter(project_id=project_id)


class TaskDetailsView(RetrieveAPIView):
    serializer_class = TaskDetailsSerializer
    lookup_url_kwarg = "task_id"

    def get_queryset(self):
    #     use pk as project id and task_id as task id
        project_id = self.kwargs.get("project_id")
        return Task.objects.filter(project_id=project_id)

