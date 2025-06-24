from django.contrib import admin
from .models import User, Skill, UserSkills

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'is_superuser', 'is_staff', 'is_premium', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('user_type', 'is_active', 'is_superuser', 'is_staff', 'is_premium', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(UserSkills)
class UserSkillsAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill')
    search_fields = ('user__email', 'skill__name')
    list_filter = ('skill',)
