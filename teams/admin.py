from django.contrib import admin
from .models import Team ,  Invitation




@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'owner__email')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'



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
