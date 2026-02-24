"""Django admin customization"""

from .models import User, Recipe, Tag, Ingredient
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Define admin page for users"""

    ordering = ["id"]
    list_display = ["name", "email"]
    fieldsets = (
        (None, {"fields": ("email", "name", "password")}),
        (
            _("Premission"),
            (
                {
                    "fields": (
                        "is_active",
                        "is_staff",
                        "is_superuser",
                    )
                }
            ),
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )
    readonly_fields = ["last_login"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "name",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredient)