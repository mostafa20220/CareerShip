from django.contrib import admin
from .models import Team, TeamProject, TeamUser, Invitation


# Inline for displaying team members inside the Team admin page
class TeamUserInline(admin.TabularInline):  # Use StackedInline for a different layout
    model = TeamUser
    extra = 1  # Allows adding one extra inline entry


# Inline for displaying projects linked to the team
class TeamProjectInline(admin.TabularInline):
    model = TeamProject
    extra = 1


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'is_private', 'created_at')
    list_filter = ('is_private', 'created_at')
    search_fields = ('name', 'created_by__username')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    inlines = [
        TeamUserInline,
        TeamProjectInline,
    ]  # Shows related users and projects inside the team page


@admin.register(TeamProject)
class TeamProjectAdmin(admin.ModelAdmin):
    list_display = ('team', 'project')
    list_filter = ('team',)
    search_fields = ('team__name', 'project__name')


@admin.register(TeamUser)
class TeamUserAdmin(admin.ModelAdmin):
    list_display = ('team', 'user')
    list_filter = ('team', 'user')
    search_fields = ('team__name', 'user__username')


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('team', 'created_by', 'created_at', 'expires_in_days', 'is_expired')
    list_filter = ('created_at',)
    search_fields = ('team__name', 'created_by__username')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    def is_expired(self, obj):
        return obj.is_expired()

    is_expired.boolean = True
