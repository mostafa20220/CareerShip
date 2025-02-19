from django.contrib import admin
from .models import *


@admin.register(DifficultyLevel)
class DifficultyLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    fields = ("name", "category", "difficulty_level", "is_premium" , "max_team_size")
    list_display = (
        "name",
        "category",
        "difficulty_level",
        "is_premium",
        "created_at",
        "max_team_size",
        "slug"
    )
    list_filter = ("category", "difficulty_level", "is_premium")
    search_fields = ("name", "slug")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "difficulty_level", "duration")
    list_filter = ("project", "difficulty_level")
    search_fields = ("name", "slug")


@admin.register(Prerequisite)
class PrerequisiteAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(TaskPrerequisite)
class TaskPrerequisiteAdmin(admin.ModelAdmin):
    list_display = ("task", "prerequisite")


@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    list_display = ("task", "method", "path")
    list_filter = ("method",)
    search_fields = ("path",)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "team", "is_pass", "created_at")
    list_filter = ("is_pass", "created_at")
    search_fields = ("user__username", "team__name")


@admin.register(UserProject)
class UserProjectAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "is_finished", "deployment_url")
    list_filter = ("is_finished",)
    search_fields = ("user__username", "project__name")
