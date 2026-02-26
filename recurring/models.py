import uuid
from django.db import models
from invoices.models import Invoice
from organizations.models import Organization


class RecurringInvoice(models.Model):
    """
    A recurring billing schedule that auto-generates invoices via Celery.
    """
    FREQ_WEEKLY = 'weekly'
    FREQ_MONTHLY = 'monthly'
    FREQ_QUARTERLY = 'quarterly'
    FREQ_ANNUALLY = 'annually'
    FREQ_CHOICES = [
        (FREQ_WEEKLY, 'Weekly'),
        (FREQ_MONTHLY, 'Monthly'),
        (FREQ_QUARTERLY, 'Quarterly'),
        (FREQ_ANNUALLY, 'Annually'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='recurring_invoices',
    )
    template_invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='recurring_schedules',
        help_text='Draft invoice used as template',
    )
    frequency = models.CharField(max_length=20, choices=FREQ_CHOICES, default=FREQ_MONTHLY)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    max_occurrences = models.IntegerField(null=True, blank=True)
    occurrences_sent = models.IntegerField(default=0)
    next_run_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Recurring Invoice'
        ordering = ['next_run_date']

    def __str__(self):
        return f'{self.template_invoice.invoice_number} — {self.get_frequency_display()}'
