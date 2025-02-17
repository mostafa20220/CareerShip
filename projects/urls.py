from django.urls import path
from .views import *

urlpatterns = [
    path("categories/", list_categories, name="categories-list"),
    path("", list_projects, name="projects-list"),
    path("<int:pk>/", get_project, name="get-project"),
    path("submit-task/", submit_task, name="submit-task"),
]
