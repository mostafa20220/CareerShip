from users.models import User


class UsersService:

    def create_user(self, user_data):
        return User.objects.create_user(**user_data)