from django.urls import path
from .views import *

urlpatterns = [
    path('list-categories/', list_categories, name='list-categories'),
]
