from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'full_name', 'is_email_verified', 'totp_enabled', 'date_joined']
    list_filter = ['is_email_verified', 'totp_enabled', 'is_staff', 'is_superuser']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('InvoiceFlow', {'fields': ('avatar', 'is_email_verified', 'totp_enabled', 'totp_secret')}),
    )
