from django.contrib import admin
from teams.models import *


# Register your models here.




class UsersInline(admin.TabularInline):
    model = TeamUser


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "is_private")
    search_fields = ("name", "is_private")
    inlines = [UsersInline]

