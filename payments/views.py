import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from invoices.models import Invoice
from .models import Payment
from .forms import PaymentForm


def get_org(request):
    m = request.user.memberships.select_related('organization').first()
    return m.organization if m else None


@login_required
def record_payment(request, invoice_pk):
    org = get_org(request)
    invoice = get_object_or_404(Invoice, pk=invoice_pk, organization=org)

    if request.method == 'POST':
        form = PaymentForm(invoice, request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()  # Payment.save() auto-updates invoice status
            messages.success(request, f'Payment of ${payment.amount} recorded.')
            return redirect('invoices:detail', pk=invoice_pk)
    else:
        form = PaymentForm(invoice)

    return render(request, 'payments/form.html', {'form': form, 'invoice': invoice})


@login_required
def stripe_checkout(request, invoice_pk):
    """Creates a Stripe Checkout session and redirects to Stripe."""
    org = get_org(request)
    invoice = get_object_or_404(Invoice, pk=invoice_pk, organization=org)

    if not settings.STRIPE_SECRET_KEY:
        messages.warning(request, 'Stripe is not configured. Please add STRIPE_SECRET_KEY to your .env file.')
        return redirect('invoices:detail', pk=invoice_pk)

    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY

    success_url = request.build_absolute_uri(f'/payments/invoice/{invoice_pk}/stripe/success/')
    cancel_url = request.build_absolute_uri(f'/invoices/portal/{invoice_pk}/')

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': invoice.client.currency.lower(),
                'product_data': {'name': f'Invoice {invoice.invoice_number} — {org.name}'},
                'unit_amount': int(invoice.balance_due * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={'invoice_pk': str(invoice_pk)},
    )
    invoice.stripe_payment_intent = session.payment_intent or session.id
    invoice.save(update_fields=['stripe_payment_intent'])
    return redirect(session.url, permanent=False)


@login_required
def stripe_success(request, invoice_pk):
    return render(request, 'payments/stripe_success.html', {'invoice_pk': invoice_pk})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhook events to auto-mark invoices as paid."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse(status=400)

    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        invoice_pk = session.get('metadata', {}).get('invoice_pk')
        if invoice_pk:
            try:
                invoice = Invoice.objects.get(pk=invoice_pk)
                Payment.objects.create(
                    invoice=invoice,
                    amount=invoice.balance_due,
                    payment_date=__import__('datetime').date.today(),
                    method='stripe',
                    stripe_charge_id=session.get('payment_intent', ''),
                    notes='Auto-recorded via Stripe webhook',
                )
            except Invoice.DoesNotExist:
                pass

    return HttpResponse(status=200)
