from rest_framework.permissions import BasePermission
from teams.services import is_team_member


class CanViewTeam(BasePermission):
    def has_object_permission(self, request, view, obj):
        # if it's public then the user can view it anyway
        return is_team_member(user=request.user , team=obj)

class IsTeamAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsTeamMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return is_team_member(user=request.user, team=obj)
