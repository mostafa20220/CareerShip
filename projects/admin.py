from django.contrib import admin

from projects.models.categories_difficulties import DifficultyLevel, Category
from projects.models.prerequisites import Prerequisite, TaskPrerequisite
from projects.models.projects import Project, UserProject
from projects.models.submission import Submission
from projects.models.tasks_endpoints import Endpoint, Task


@admin.register(DifficultyLevel)
class DifficultyLevelAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    list_display = ("task", "method", "path")
    list_filter = ("method",)
    search_fields = ("path",)


class TaskInline(admin.TabularInline):  # or use StackedInline for a different look
    model = Task
    extra = 1


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
    inlines = [TaskInline]

class EndpointInline(admin.TabularInline):
    model = Endpoint
    extra = 1

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "difficulty_level", "duration_in_days")
    list_filter = ("project", "difficulty_level")
    search_fields = ("name", "slug")
    inlines = [EndpointInline]


@admin.register(Prerequisite)
class PrerequisiteAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(TaskPrerequisite)
class TaskPrerequisiteAdmin(admin.ModelAdmin):
    list_display = ("task", "prerequisite")



@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "team", "status","passed_percentage","execution_logs","feedback" ,"deployment_url", "github_url","completed_at","created_at" )
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "team__name")


@admin.register(UserProject)
class UserProjectAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "is_finished", "deployment_url")
    list_filter = ("is_finished",)
    search_fields = ("user__username", "project__name")
