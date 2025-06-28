from django.contrib import admin
from django.db import models
from django.forms import Textarea

from projects.models.categories_difficulties import DifficultyLevel, Category
from projects.models.prerequisites import Prerequisite, TaskPrerequisite
from projects.models.projects import Project, TeamProject
from projects.models.submission import Submission
from projects.models.tasks_endpoints import Endpoint, Task
from projects.models.testcases import TestCase, ApiTestCase # Import both new models

# Define a custom widget override for all JSONFields to make them bigger
JSON_TEXTAREA_OVERRIDE = {
    models.JSONField: {'widget': Textarea(attrs={'rows': 10, 'cols': 80})},
}

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

@admin.register(Prerequisite)
class PrerequisiteAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(TaskPrerequisite)
class TaskPrerequisiteAdmin(admin.ModelAdmin):
    list_display = ("task", "prerequisite")

@admin.register(TeamProject)
class TeamProjectAdmin(admin.ModelAdmin):
    list_display = ("team", "project", "is_finished")
    list_filter = ("is_finished",)
    search_fields = ("team__name", "project__name")


# --- Inlines for Declarative Test Cases ---

class ApiTestCaseInline(admin.StackedInline):
    model = ApiTestCase
    extra = 1
    # Use the JSON widget override
    formfield_overrides = JSON_TEXTAREA_OVERRIDE
    # You can specify the field order if you like
    fields = ('endpoint', 'expected_status_code', 'request_payload', 'request_headers', 'expected_response_schema')


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'order','task', 'test_type', 'points', 'stop_on_failure')
    list_filter = ('test_type', 'task__project__name')
    search_fields = ('name', 'task__name')
    inlines = [ApiTestCaseInline]
    # Specify the field order for the main TestCase form
    fields = ('task', 'name', 'description', 'test_type', 'points', 'stop_on_failure')


# --- Inlines for Project and Task Admins ---

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1
    fields = ('name', 'order','slug', 'difficulty_level', 'duration_in_days')
    show_change_link = True

class EndpointInline(admin.TabularInline):
    model = Endpoint
    extra = 1

class TestCaseInlineForTask(admin.TabularInline):
    model = TestCase
    extra = 1
    fields = ('name','order', 'test_type', 'points', 'stop_on_failure')
    show_change_link = True


# --- Main Project and Task Admins (Updated) ---

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "difficulty_level",
        "is_premium",
        "max_team_size",
        "created_at",
    )
    list_filter = ("category", "difficulty_level", "is_premium")
    search_fields = ("name", "slug")
    inlines = [TaskInline]
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "order","project", "difficulty_level", "duration_in_days")
    list_filter = ("project__name", "difficulty_level")
    search_fields = ("name", "slug")
    inlines = [EndpointInline, TestCaseInlineForTask]
    prepopulated_fields = {'slug': ('name',)}


# --- Submission Admin (Updated for better JSON editing) ---

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "status", "passed_percentage", "completed_at", "created_at")
    list_filter = ("status", "created_at", "task__project__name")
    search_fields = ("user__username", "task__name")
    readonly_fields = ('created_at', 'completed_at')
    formfield_overrides = JSON_TEXTAREA_OVERRIDE
