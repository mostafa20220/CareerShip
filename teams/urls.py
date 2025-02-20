from django.urls import path
from . import views

urlpatterns = [
    # Other URL patterns
    path('invite/<int:pk>/', views.InvitationDetailView, name='invitation_detail'),
    path('accept/<int:pk>/', views.AcceptInvitationView, name='accept_invitation'),
    path('create/' , views.CreateTeamView.as_view(), name='create_team' ),
]