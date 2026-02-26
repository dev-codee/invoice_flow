import uuid
from django.db import models
from invoices.models import Invoice


class Payment(models.Model):
    """
    Records a payment (full or partial) against an invoice.
    """
    METHOD_STRIPE = 'stripe'
    METHOD_BANK_TRANSFER = 'bank_transfer'
    METHOD_CASH = 'cash'
    METHOD_CHEQUE = 'cheque'

    METHOD_CHOICES = [
        (METHOD_STRIPE, 'Stripe (Online)'),
        (METHOD_BANK_TRANSFER, 'Bank Transfer'),
        (METHOD_CASH, 'Cash'),
        (METHOD_CHEQUE, 'Cheque'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='payments',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    stripe_charge_id = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Payment'
        ordering = ['-payment_date']

    def __str__(self):
        return f'Payment {self.amount} for {self.invoice.invoice_number}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update invoice amount_paid and status
        invoice = self.invoice
        total_paid = invoice.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        invoice.amount_paid = total_paid
        if total_paid >= invoice.total:
            invoice.status = Invoice.STATUS_PAID
        elif total_paid > 0:
            invoice.status = Invoice.STATUS_PARTIALLY_PAID
        invoice.save(update_fields=['amount_paid', 'status'])
