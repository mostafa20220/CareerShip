from django.urls import path, include
from rest_framework.routers import DefaultRouter

from projects.views.categories_difficulties import list_categories, ListDifficultiesView
from projects.views.projects import ProjectsListView, ProjectDetailsView, ProjectSeedUploadView, request_certificate, \
    certificate_available
from projects.views.registration import ProjectRegistrationViewSet

from projects.views.submission import SubmissionViewSet
from projects.views.tasks import TaskDetailsView, ListTasksView

router = DefaultRouter()
router.register(r'registrations', ProjectRegistrationViewSet, basename='project-registration')
router.register(r'(?P<project_id>\d+)/tasks/(?P<task_id>\d+)/submissions', SubmissionViewSet, basename='task-submissions')

urlpatterns = [
    path("categories/", list_categories, name="list-categories"),
    path("difficulties/", ListDifficultiesView.as_view(), name="list-difficulties"),

    path("projects/", include([
        path("", ProjectsListView.as_view(), name="list-projects"),
        path('upload-seed/', ProjectSeedUploadView.as_view(), name='project-upload-seed'),
        path("<int:project_id>/", ProjectDetailsView.as_view(), name="project-details"),
        path("<int:project_id>/submissions", SubmissionViewSet.as_view({'get': 'list'}), name="list-project-submissions"),
        path("<int:project_id>/tasks/", ListTasksView.as_view(), name="list-project-tasks"),
        path("<int:project_id>/tasks/<int:task_id>/", TaskDetailsView.as_view(), name="task-details"),
        path("<int:project_id>/certificates/request/", request_certificate, name="request-certificate"),
        path("<int:project_id>/certificates/available/", certificate_available, name="certificate-available"),
        path("", include(router.urls)),
    ])),
]
