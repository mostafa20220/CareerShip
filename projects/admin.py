from django.contrib import admin
from django.db import models
from django.forms import Textarea

from projects.models.categories_difficulties import DifficultyLevel, Category
from projects.models.prerequisites import Prerequisite, TaskPrerequisite
from projects.models.projects import Project, TeamProject, ScreenshotComparison, TaskReferenceImage
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


# --- Frontend Reference Images Admin ---

@admin.register(TaskReferenceImage)
class TaskReferenceImageAdmin(admin.ModelAdmin):
    list_display = ("task", "device_type", "viewport_width", "viewport_height", "created_at")
    list_filter = ("task__project__name", "viewport_width", "viewport_height")
    search_fields = ("task__name", "description")
    readonly_fields = ("created_at", "device_type")
    
    fieldsets = (
        (None, {
            'fields': ('task', 'description', 'image')
        }),
        ('Viewport Settings', {
            'fields': ('viewport_width', 'viewport_height', 'device_type'),
            'description': 'Screenshot viewport dimensions for comparison'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(ScreenshotComparison)
class ScreenshotComparisonAdmin(admin.ModelAdmin):
    list_display = ("team_project", "reference_image", "similarity_score", "status", "created_at")
    list_filter = ("status", "created_at", "team_project__project__name")
    search_fields = ("team_project__team__name", "feedback_text")
    readonly_fields = ("created_at", "similarity_score", "feedback_text", "screenshot")

    fieldsets = (
        (None, {
            'fields': ('team_project', 'reference_image', 'status')
        }),
        ('Comparison Results', {
            'fields': ('similarity_score', 'feedback_text'),
            'classes': ('collapse',)
        }),
        ('Images', {
            'fields': ('screenshot',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def has_add_permission(self, request):
        # Prevent manual creation of screenshot comparisons
        return False


# --- Inlines for Declarative Test Cases ---

class ApiTestCaseInline(admin.StackedInline):
    model = ApiTestCase
    extra = 1
    # Use the JSON widget override
    formfield_overrides = JSON_TEXTAREA_OVERRIDE
    # You can specify the field order if you like
    fields = ('endpoint', 'expected_status_code', 'request_payload', 'request_headers', 'expected_response_schema')


class ReferenceImageInline(admin.TabularInline):
    model = TaskReferenceImage
    extra = 1
    fields = ('image', 'viewport_width', 'viewport_height', 'description')
    readonly_fields = ('device_type',)
    show_change_link = True


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'order','task', 'test_type', 'points', 'stop_on_failure')
    list_filter = ('test_type', 'task__project__name')
    search_fields = ('name', 'task__name')
    inlines = [ApiTestCaseInline]
    # Specify the field order for the main TestCase form
    fields = ('task', 'name', 'description', 'test_type', 'order', 'points', 'stop_on_failure' , 'input_data', 'command_args', 'expected_output')

    def check_order(self, request, obj, form, change):
        # Get the task from the form
        task = form.cleaned_data.get('task')
        order = form.cleaned_data.get('order')

        # Check if there's already a test case with this order for the same task
        if task and order:
            existing = TestCase.objects.filter(task=task, order=order)
            if change:  # If editing existing object
                existing = existing.exclude(pk=obj.pk)
            if existing.exists():
                from django.core.exceptions import ValidationError
                raise ValidationError('A test case with this order already exists for this task.')


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
    inlines = [EndpointInline, TestCaseInlineForTask, ReferenceImageInline]
    prepopulated_fields = {'slug': ('name',)}
    
    def get_inlines(self, request, obj):
        """Show ReferenceImageInline only for frontend projects"""
        inlines = [EndpointInline, TestCaseInlineForTask]
        
        # Show reference images for frontend projects or all projects (you can adjust this logic)
        if obj and obj.project.category.name.lower() in ['frontend', 'web', 'ui', 'react', 'vue', 'angular']:
            inlines.append(ReferenceImageInline)
            
        return inlines


# --- Submission Admin (Updated for better JSON editing) ---

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "status", "passed_percentage", "completed_at", "created_at")
    list_filter = ("status", "created_at", "task__project__name")
    search_fields = ("user__username", "task__name")
    readonly_fields = ('created_at', 'completed_at')
    formfield_overrides = JSON_TEXTAREA_OVERRIDE
    
    fieldsets = (
        (None, {
            'fields': ('project', 'task', 'team', 'user', 'status')
        }),
        ('URLs & Code', {
            'fields': ('deployment_url', 'github_url', 'language', 'code'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('passed_tests', 'passed_percentage', 'execution_logs', 'feedback'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )