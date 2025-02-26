from django.urls import path
from . import views

'''
URLS




** invitation
teams/team_id/invite/         POST-> generate invitation with invitation link,
teams/invite/invite_id        -> GET 
teams/invite/invite_id/accept -> accept the invitation,


'''




urlpatterns = [
    path('create/' , views.CreateTeamView.as_view(), name='create_team' ),
    path('leave/' , views.LeaveTeamView.as_view(), name='leave_team' ),
    path("<int:pk>/", views.TeamDetailUpdateView.as_view(), name="team-get-update-detail"),
    path("<int:pk>/invite/", views.GenerateInviteView.as_view(), name="generate-invitation"),
    path("invite/<int:pk>/", views.InvitationDetailView.as_view(), name="invitation-detail"),
    path("invite/<int:invite_id>/accept/", views.AcceptInvitationView.as_view(), name="accept-invitation"),
    path("", views.ListTeams.as_view(), name='list-teams'),
]