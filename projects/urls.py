from django.urls import path
from .views import *

urlpatterns = [
    path('list-categories/', list_categories, name='list-categories'),
    path('list-projects/', list_projects, name='list-projects'),
    path('get-project/<str:pk>/', get_project, name='get-project'),
    path('submit-task/', submit_task, name='submit-task'),
]
