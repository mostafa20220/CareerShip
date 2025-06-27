from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

class UUIDRouter(DefaultRouter):
    def get_lookup_regex(self, viewset, lookup_prefix=''):
        # Override to use uuid in the URL path
        return r'(?P<uuid>[^/.]+)'
    def get_lookup_field(self, viewset):
        # Override to use uuid as the lookup field
        return 'uuid'

router = UUIDRouter()
router.register('', views.TeamViewSet, basename='team')

urlpatterns = router.urls + [
    # Team invitations endpoints
    path('<uuid:team_pk>/invitations/', views.InvitationViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='team-invitations-list'),

    path('<uuid:team_pk>/invitations/<uuid:pk>/', views.InvitationViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='team-invitations-detail'),

    path('<uuid:team_pk>/invitations/<uuid:pk>/accept/', views.InvitationViewSet.as_view({
        'post': 'accept'
    }), name='team-invitations-accept'),

    path('<uuid:team_pk>/invitations/<uuid:pk>/disable/', views.InvitationViewSet.as_view({
        'post': 'disable'
    }), name='team-invitations-disable'),

    path('<uuid:team_pk>/invitations/<uuid:pk>/enable/', views.InvitationViewSet.as_view({
        'post': 'enable'
    }), name='team-invitations-enable'),
]
