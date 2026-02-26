import uuid
from django.db import models
from organizations.models import Organization


class ReminderRule(models.Model):
    """
    Configurable automated email reminder rule per organization.
    """
    TRIGGER_BEFORE_DUE = 'before_due'
    TRIGGER_ON_DUE = 'on_due'
    TRIGGER_AFTER_DUE = 'after_due'
    TRIGGER_CHOICES = [
        (TRIGGER_BEFORE_DUE, 'Before Due Date'),
        (TRIGGER_ON_DUE, 'On Due Date'),
        (TRIGGER_AFTER_DUE, 'After Due Date (Overdue)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='reminder_rules',
    )
    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES)
    days_offset = models.IntegerField(
        default=0, help_text='Number of days before/after due date to send reminder',
    )
    is_active = models.BooleanField(default=True)
    subject_template = models.CharField(max_length=200, default='Payment reminder for invoice {invoice_number}')
    body_template = models.TextField(
        default='Dear {client_name},\n\nThis is a reminder that invoice {invoice_number} '
                'for {amount} is due on {due_date}.\n\nThank you.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reminder Rule'
        ordering = ['trigger', 'days_offset']

    def __str__(self):
        return f'{self.organization.name} — {self.get_trigger_display()} ({self.days_offset}d)'
