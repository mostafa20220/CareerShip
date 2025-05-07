from rest_framework.permissions import BasePermission

from teams.services import is_team_member


class CanViewTeam(BasePermission):
    def has_object_permission(self, request, view, obj):
        # if it's public then the user can view it anyway
        if not obj.is_private:
            return True
        # Allow if a user is a member
        return is_team_member(user=request.user , team=obj)