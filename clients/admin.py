from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'organization', 'currency', 'is_active', 'created_at']
    list_filter = ['organization', 'currency', 'is_active']
    search_fields = ['name', 'email', 'phone']
    list_select_related = ['organization']
