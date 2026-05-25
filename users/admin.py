from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.forms import AdminUserChangeForm, AdminUserCreationForm
from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = AdminUserCreationForm
    form = AdminUserChangeForm
    list_display = ("email", "name", "surname", "phone", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser")
    ordering = ("email",)
    search_fields = ("email", "name", "surname", "phone")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Личные данные",
            {"fields": ("name", "surname", "avatar", "phone", "github_url", "about", "favorites")},
        ),
        ("Права", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Важные даты", {"fields": ("last_login", "date_joined", "created_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "surname", "phone", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions", "favorites")
