import uuid
from django.db import models
from django.conf import settings


class Organization(models.Model):
    """
    Represents a tenant / business account on InvoiceFlow.
    """
    PLAN_FREE = 'free'
    PLAN_PRO = 'pro'
    PLAN_ENTERPRISE = 'enterprise'
    PLAN_CHOICES = [
        (PLAN_FREE, 'Free'),
        (PLAN_PRO, 'Pro'),
        (PLAN_ENTERPRISE, 'Enterprise'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_organizations',
    )
    logo = models.ImageField(upload_to='org_logos/', null=True, blank=True)
    address = models.TextField(blank=True)
    currency = models.CharField(max_length=3, default='USD')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    payment_terms = models.IntegerField(default=30, help_text='Default net days')
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return self.name

    @property
    def free_tier_limits(self):
        return {'clients': 5, 'invoices_per_month': 20}


class OrganizationMembership(models.Model):
    """
    Links a User to an Organization with a specific role.
    """
    ROLE_OWNER = 'owner'
    ROLE_ADMIN = 'admin'
    ROLE_STAFF = 'staff'
    ROLE_CHOICES = [
        (ROLE_OWNER, 'Owner'),
        (ROLE_ADMIN, 'Admin'),
        (ROLE_STAFF, 'Staff'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_STAFF)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'organization')
        verbose_name = 'Organization Membership'

    def __str__(self):
        return f'{self.user.email} @ {self.organization.name} ({self.role})'


class Invitation(models.Model):
    """
    Pending email invitation to join an organization.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invitations',
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
    )
    email = models.EmailField()
    role = models.CharField(max_length=10, choices=OrganizationMembership.ROLE_CHOICES, default='staff')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Invitation'

    def __str__(self):
        return f'Invite {self.email} → {self.organization.name}'
