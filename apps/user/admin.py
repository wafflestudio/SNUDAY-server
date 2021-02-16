from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from apps.user.models import User


class UserCreateForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    add_form = UserCreateForm
    form = CustomUserChangeForm
    fields = ("username", "email", "first_name", "last_name", "password", "id")
    readonly_fields = ("id",)

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "first_name",
                    "last_name",
                    "username",
                    "email",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
