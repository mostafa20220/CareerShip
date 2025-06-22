from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "no", "created_at")
    list_filter = ("created_at", "project__category", "project__difficulty_level")
    search_fields = ("user__first_name", "user__last_name", "user__email", "project__name", "no")
    readonly_fields = ("no", "created_at")
    ordering = ("-created_at",)
    
    fieldsets = (
        ("Certificate Information", {
            "fields": ("no", "created_at")
        }),
        ("User & Project", {
            "fields": ("user", "project")
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "project", "project__category", "project__difficulty_level")
