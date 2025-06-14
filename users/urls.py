from django.urls import path, include

from users.views import (
    LogoutView,
    RegisterView,
    ProfileView,
    GoogleLoginView,
    GitHubLoginView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    # Social Authentication URLs
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('dj-rest-auth/google/', GoogleLoginView.as_view(), name='google_login'),
    path('dj-rest-auth/github/', GitHubLoginView.as_view(), name='github_login'),
]
