from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

PERMISSION_ERROR_MESSAGE = 'You do not have permission to perform this action.'

class IsStudent(BasePermission):
    message = PERMISSION_ERROR_MESSAGE

    def has_permission(self, request, view):
        if not (request.user.is_authenticated and request.user.is_student()):
            raise PermissionDenied(self.message)
        return True

class IsAdmin(BasePermission):
    message = PERMISSION_ERROR_MESSAGE

    def has_permission(self, request, view):
        if not (request.user.is_authenticated and request.user.is_admin()):
            raise PermissionDenied(self.message)
        return True