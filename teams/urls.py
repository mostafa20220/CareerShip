from django.urls import path
from . import views

urlpatterns = [
    # Other URL patterns
    path('invite/<int:pk>/', views.invitation_view, name='invitation_detail'),
]