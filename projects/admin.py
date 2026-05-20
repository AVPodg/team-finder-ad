from django.contrib import admin

from projects.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "description", "owner__email", "owner__name", "owner__surname")
    autocomplete_fields = ("owner", "participants")
    filter_horizontal = ("participants", "skills")

# Register your models here.
