import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    In-app notification for users (payment received, invoice viewed, etc).
    """
    TYPE_PAYMENT = 'payment_received'
    TYPE_VIEWED = 'invoice_viewed'
    TYPE_REMINDER = 'reminder_sent'
    TYPE_INVITE = 'invitation'
    TYPE_CHOICES = [
        (TYPE_PAYMENT, 'Payment Received'),
        (TYPE_VIEWED, 'Invoice Viewed'),
        (TYPE_REMINDER, 'Reminder Sent'),
        (TYPE_INVITE, 'Invitation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    message = models.CharField(max_length=500)
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.notification_type}] {self.user.email}: {self.message[:50]}'
