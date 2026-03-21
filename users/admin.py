from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'last_name', 'first_name', 'patronymic', 'is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email', 'last_name', 'first_name', 'patronymic')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('last_name', 'first_name', 'patronymic')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'last_name', 'first_name', 'patronymic', 'password1', 'password2', 'is_staff', 'is_active')
        }),
    )


admin.site.register(University)
