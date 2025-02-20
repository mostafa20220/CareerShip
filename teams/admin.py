from django.contrib import admin
from teams.models import *

from users.models import User
# Register your models here.




class UsersInline(admin.TabularInline):
    model = User


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "is_private", "description")
    search_fields = ("name", "is_private", "description")
    inlines = [UsersInline]

