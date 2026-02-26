import uuid
from django.db import models
from organizations.models import Organization


class Client(models.Model):
    """
    A business client belonging to a tenant (Organization).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='clients',
    )
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    billing_address = models.TextField(blank=True)
    currency = models.CharField(max_length=3, default='USD')
    tax_id = models.CharField(max_length=50, blank=True, verbose_name='VAT / Tax ID')
    notes = models.TextField(blank=True, help_text='Internal notes — not shown on invoices')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Client'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def outstanding_balance(self):
        """Sum of unpaid invoice totals for this client."""
        from invoices.models import Invoice
        return Invoice.objects.filter(
            client=self,
            status__in=['sent', 'viewed', 'partially_paid', 'overdue'],
        ).aggregate(
            total=models.Sum(models.F('total') - models.F('amount_paid'))
        )['total'] or 0
