import uuid
from django.db import models
from django.utils import timezone
from organizations.models import Organization
from clients.models import Client


class Invoice(models.Model):
    """
    Core invoice model — full lifecycle from Draft to Paid.
    """
    STATUS_DRAFT = 'draft'
    STATUS_SENT = 'sent'
    STATUS_VIEWED = 'viewed'
    STATUS_PARTIALLY_PAID = 'partially_paid'
    STATUS_PAID = 'paid'
    STATUS_OVERDUE = 'overdue'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SENT, 'Sent'),
        (STATUS_VIEWED, 'Viewed'),
        (STATUS_PARTIALLY_PAID, 'Partially Paid'),
        (STATUS_PAID, 'Paid'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='invoices',
    )
    client = models.ForeignKey(
        Client, on_delete=models.PROTECT, related_name='invoices',
    )
    invoice_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    pdf_file = models.FileField(upload_to='invoices/pdfs/', null=True, blank=True)
    stripe_payment_intent = models.CharField(max_length=200, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Invoice'
        ordering = ['-created_at']
        unique_together = ('organization', 'invoice_number')

    def __str__(self):
        return f'{self.invoice_number} — {self.client.name}'

    @property
    def balance_due(self):
        return max(self.total - self.amount_paid, 0)

    @property
    def is_overdue(self):
        from datetime import date
        return (
            self.status not in [self.STATUS_PAID, self.STATUS_CANCELLED]
            and self.due_date < date.today()
        )

    def recalculate_totals(self):
        """Recompute subtotal, tax, and total from line items."""
        items = self.line_items.all()
        subtotal = sum(item.amount for item in items)
        tax_amount = sum(
            item.amount * (item.tax_rate / 100) for item in items
        )
        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.total = subtotal + tax_amount - self.discount_amount
        self.save(update_fields=['subtotal', 'tax_amount', 'total'])

    @classmethod
    def generate_invoice_number(cls, organization):
        """Auto-generate sequential invoice number per org (INV-0001)."""
        last = cls.objects.filter(organization=organization).order_by('-created_at').first()
        if last and last.invoice_number.startswith('INV-'):
            try:
                num = int(last.invoice_number.split('-')[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1
        return f'INV-{num:04d}'


class InvoiceLineItem(models.Model):
    """
    A single line item within an invoice.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='line_items',
    )
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                   help_text='Discount percentage')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Invoice Line Item'
        ordering = ['id']

    def __str__(self):
        return f'{self.description} × {self.quantity}'

    def save(self, *args, **kwargs):
        # Compute amount: qty × unit_price × (1 - discount%) 
        base = self.quantity * self.unit_price
        base_after_discount = base * (1 - self.discount / 100)
        self.amount = round(base_after_discount, 2)
        super().save(*args, **kwargs)
