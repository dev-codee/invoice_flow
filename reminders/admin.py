from django.contrib import admin
from .models import ReminderRule


@admin.register(ReminderRule)
class ReminderRuleAdmin(admin.ModelAdmin):
    list_display = ['organization', 'trigger', 'days_offset', 'is_active']
    list_filter = ['trigger', 'is_active', 'organization']
