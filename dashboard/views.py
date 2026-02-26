from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.utils import timezone


def get_active_org(request):
    """Get the first organization the user belongs to."""
    membership = request.user.memberships.select_related('organization').first()
    return membership.organization if membership else None


def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    return redirect('/accounts/login/')


@login_required
def dashboard(request):
    org = get_active_org(request)
    if not org:
        return redirect('organizations:settings')

    from invoices.models import Invoice
    from clients.models import Client

    invoices = Invoice.objects.filter(organization=org)
    today = timezone.now().date()

    total_invoiced = invoices.aggregate(t=Sum('total'))['t'] or 0
    total_collected = invoices.aggregate(t=Sum('amount_paid'))['t'] or 0
    total_outstanding = invoices.filter(
        status__in=['sent', 'viewed', 'partially_paid', 'overdue']
    ).aggregate(t=Sum('total') - Sum('amount_paid'))['t'] or 0
    total_overdue = invoices.filter(
        status='overdue'
    ).aggregate(t=Sum('total') - Sum('amount_paid'))['t'] or 0

    recent_invoices = invoices.select_related('client').order_by('-created_at')[:8]

    top_clients = (
        Client.objects.filter(organization=org)
        .annotate(total_invoiced=Sum('invoices__total'))
        .order_by('-total_invoiced')[:5]
    )

    context = {
        'org': org,
        'total_invoiced': total_invoiced,
        'total_collected': total_collected,
        'total_outstanding': total_outstanding,
        'total_overdue': total_overdue,
        'recent_invoices': recent_invoices,
        'top_clients': top_clients,
    }
    return render(request, 'dashboard/index.html', context)
