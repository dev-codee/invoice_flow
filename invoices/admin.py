from django.contrib import admin
from .models import Invoice, InvoiceLineItem


class LineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 1
    readonly_fields = ['amount']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client', 'organization', 'status', 'total', 'amount_paid', 'due_date']
    list_filter = ['status', 'organization', 'issue_date']
    search_fields = ['invoice_number', 'client__name']
    readonly_fields = ['subtotal', 'tax_amount', 'total', 'amount_paid', 'invoice_number']
    inlines = [LineItemInline]
    date_hierarchy = 'issue_date'


@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'unit_price', 'amount']
    readonly_fields = ['amount']
