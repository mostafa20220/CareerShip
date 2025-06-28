from rest_framework.permissions import BasePermission
class IsStudent(BasePermission):
    """Allows access only to users with user_type 'student'."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_student())

class IsAdmin(BasePermission):
    """Allows access only to users with user_type 'admin'."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and  request.user.is_admin())