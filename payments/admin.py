from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'method', 'payment_date', 'stripe_charge_id']
    list_filter = ['method', 'payment_date']
    search_fields = ['invoice__invoice_number', 'stripe_charge_id']
    date_hierarchy = 'payment_date'
