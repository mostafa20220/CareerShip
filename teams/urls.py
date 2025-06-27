from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.TeamViewSet, basename='team')

urlpatterns = router.urls + [
    # Team invitations endpoints
    path('<int:team_pk>/invitations/', views.InvitationViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='team-invitations-list'),

    path('<int:team_pk>/invitations/<uuid:pk>/', views.InvitationViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='team-invitations-detail'),

    path('<int:team_pk>/invitations/<uuid:pk>/accept/', views.InvitationViewSet.as_view({
        'post': 'accept'
    }), name='team-invitations-accept'),

    path('<int:team_pk>/invitations/<uuid:pk>/disable/', views.InvitationViewSet.as_view({
        'post': 'disable'
    }), name='team-invitations-disable'),
#     enable endpoint
    path('<int:team_pk>/invitations/<uuid:pk>/enable/', views.InvitationViewSet.as_view({
        'post': 'enable'
    }), name='team-invitations-enable'),
]

