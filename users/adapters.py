from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_username
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # If user is already logged in, no action needed
        if request.user.is_authenticated:
            return

        # Try to find existing user with the same email
        email = user_email(sociallogin.user)
        if not email:
            return

        try:
            existing_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return

        # Link this social account to the existing user
        sociallogin.connect(request, existing_user)