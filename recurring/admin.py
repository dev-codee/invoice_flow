from django.contrib import admin
from .models import RecurringInvoice


@admin.register(RecurringInvoice)
class RecurringInvoiceAdmin(admin.ModelAdmin):
    list_display = ['template_invoice', 'organization', 'frequency', 'next_run_date', 'is_active', 'occurrences_sent']
    list_filter = ['frequency', 'is_active', 'organization']
    search_fields = ['template_invoice__invoice_number']
