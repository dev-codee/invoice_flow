import io
from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, FileResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q
from .models import Invoice, InvoiceLineItem
from .forms import InvoiceForm, LineItemFormSet
from django.conf import settings


def get_org(request):
    m = request.user.memberships.select_related('organization').first()
    return m.organization if m else None


@login_required
def invoice_list(request):
    org = get_org(request)
    qs = Invoice.objects.filter(organization=org).select_related('client')
    status_filter = request.GET.get('status', '')
    q = request.GET.get('q', '')
    if status_filter:
        qs = qs.filter(status=status_filter)
    if q:
        qs = qs.filter(Q(invoice_number__icontains=q) | Q(client__name__icontains=q))
    return render(request, 'invoices/list.html', {
        'invoices': qs, 'status_filter': status_filter, 'q': q,
        'statuses': Invoice.STATUS_CHOICES,
    })


@login_required
def invoice_create(request):
    org = get_org(request)
    if request.method == 'POST':
        form = InvoiceForm(org, request.POST)
        formset = LineItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.organization = org
            invoice.invoice_number = Invoice.generate_invoice_number(org)
            invoice.issue_date = invoice.issue_date or date.today()
            if not invoice.due_date:
                invoice.due_date = date.today() + timedelta(days=org.payment_terms)
            invoice.save()
            formset.instance = invoice
            formset.save()
            invoice.recalculate_totals()
            messages.success(request, f'Invoice {invoice.invoice_number} created.')
            return redirect('invoices:detail', pk=invoice.pk)
    else:
        from clients.models import Client
        default_due = date.today() + timedelta(days=org.payment_terms)
        form = InvoiceForm(org, initial={'issue_date': date.today(), 'due_date': default_due})
        formset = LineItemFormSet()
    return render(request, 'invoices/form.html', {
        'form': form, 'formset': formset, 'title': 'New Invoice', 'org': org,
    })


@login_required
def invoice_detail(request, pk):
    org = get_org(request)
    invoice = get_object_or_404(Invoice, pk=pk, organization=org)
    return render(request, 'invoices/detail.html', {'invoice': invoice, 'org': org})


@login_required
def invoice_update(request, pk):
    org = get_org(request)
    invoice = get_object_or_404(Invoice, pk=pk, organization=org)
    if invoice.status not in ['draft', 'sent']:
        messages.warning(request, 'Can only edit Draft or Sent invoices.')
        return redirect('invoices:detail', pk=pk)
    if request.method == 'POST':
        form = InvoiceForm(org, request.POST, instance=invoice)
        formset = LineItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            invoice.recalculate_totals()
            messages.success(request, 'Invoice updated.')
            return redirect('invoices:detail', pk=pk)
    else:
        form = InvoiceForm(org, instance=invoice)
        formset = LineItemFormSet(instance=invoice)
    return render(request, 'invoices/form.html', {
        'form': form, 'formset': formset, 'title': f'Edit {invoice.invoice_number}', 'invoice': invoice,
    })


@login_required
def invoice_delete(request, pk):
    org = get_org(request)
    invoice = get_object_or_404(Invoice, pk=pk, organization=org)
    if request.method == 'POST':
        invoice.status = Invoice.STATUS_CANCELLED
        invoice.save()
        messages.success(request, f'Invoice {invoice.invoice_number} cancelled.')
        return redirect('invoices:list')
    return render(request, 'invoices/confirm_delete.html', {'invoice': invoice})


@login_required
def invoice_send(request, pk):
    org = get_org(request)
    invoice = get_object_or_404(Invoice, pk=pk, organization=org)
    portal_url = request.build_absolute_uri(f'/invoices/portal/{invoice.pk}/')
    subject = f'Invoice {invoice.invoice_number} from {org.name}'
    body = render_to_string('invoices/email_body.txt', {'invoice': invoice, 'org': org, 'portal_url': portal_url})
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invoice.client.email],
        fail_silently=False,
    )
    invoice.status = Invoice.STATUS_SENT
    invoice.sent_at = timezone.now()
    invoice.save(update_fields=['status', 'sent_at'])
    messages.success(request, f'Invoice sent to {invoice.client.email}')
    return redirect('invoices:detail', pk=pk)


@login_required
def invoice_pdf(request, pk):
    org = get_org(request)
    invoice = get_object_or_404(Invoice, pk=pk, organization=org)
    pdf_bytes = _generate_pdf(invoice, org)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
    return response


@login_required
def invoice_duplicate(request, pk):
    org = get_org(request)
    original = get_object_or_404(Invoice, pk=pk, organization=org)
    new_invoice = Invoice.objects.create(
        organization=org,
        client=original.client,
        invoice_number=Invoice.generate_invoice_number(org),
        status=Invoice.STATUS_DRAFT,
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=org.payment_terms),
        notes=original.notes,
        terms=original.terms,
        discount_amount=original.discount_amount,
    )
    for item in original.line_items.all():
        InvoiceLineItem.objects.create(
            invoice=new_invoice,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            tax_rate=item.tax_rate,
            discount=item.discount,
        )
    new_invoice.recalculate_totals()
    messages.success(request, f'Duplicated as {new_invoice.invoice_number}')
    return redirect('invoices:detail', pk=new_invoice.pk)


def invoice_portal(request, pk):
    """Public client-facing portal — no login required."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status == Invoice.STATUS_SENT and not invoice.viewed_at:
        invoice.viewed_at = timezone.now()
        invoice.status = Invoice.STATUS_VIEWED
        invoice.save(update_fields=['viewed_at', 'status'])
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    return render(request, 'invoices/portal.html', {
        'invoice': invoice,
        'org': invoice.organization,
        'stripe_public_key': stripe_public_key,
    })


def _generate_pdf(invoice, org):
    """Generate a PDF invoice using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    primary = colors.HexColor('#4f46e5')
    story = []

    # Header
    header_data = [
        [Paragraph(f'<font size="22" color="#4f46e5"><b>InvoiceFlow</b></font>', styles['Normal']),
         Paragraph(f'<font size="18"><b>INVOICE</b></font><br/>'
                   f'<font size="10" color="grey">{invoice.invoice_number}</font>', styles['Normal'])]
    ]
    header_table = Table(header_data, colWidths=[100*mm, 70*mm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10*mm))

    # Org / Client info
    info_data = [
        [Paragraph(f'<b>{org.name}</b><br/>{org.address or ""}<br/>{org.phone or ""}', styles['Normal']),
         Paragraph(f'<b>Bill To:</b><br/>{invoice.client.name}<br/>{invoice.client.email}<br/>'
                   f'{invoice.client.billing_address or ""}', styles['Normal'])]
    ]
    info_table = Table(info_data, colWidths=[90*mm, 80*mm])
    story.append(info_table)
    story.append(Spacer(1, 8*mm))

    # Dates
    dates_data = [
        ['Issue Date', str(invoice.issue_date)],
        ['Due Date', str(invoice.due_date)],
        ['Status', invoice.get_status_display()],
    ]
    dates_table = Table(dates_data, colWidths=[50*mm, 50*mm])
    dates_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(dates_table)
    story.append(Spacer(1, 10*mm))

    # Line items
    item_data = [['Description', 'Qty', 'Unit Price', 'Tax %', 'Discount %', 'Amount']]
    for item in invoice.line_items.all():
        item_data.append([
            item.description,
            str(item.quantity),
            f'${item.unit_price:.2f}',
            f'{item.tax_rate}%',
            f'{item.discount}%',
            f'${item.amount:.2f}',
        ])
    items_table = Table(item_data, colWidths=[80*mm, 18*mm, 26*mm, 18*mm, 22*mm, 22*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 8*mm))

    # Totals
    totals_data = [
        ['Subtotal', f'${invoice.subtotal:.2f}'],
        ['Discount', f'-${invoice.discount_amount:.2f}'],
        ['Tax', f'${invoice.tax_amount:.2f}'],
        ['TOTAL DUE', f'${invoice.total:.2f}'],
    ]
    totals_table = Table(totals_data, colWidths=[120*mm, 30*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 13),
        ('BACKGROUND', (0, -1), (-1, -1), primary),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('LINEABOVE', (0, -1), (-1, -1), 1, primary),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(totals_table)

    if invoice.notes:
        story.append(Spacer(1, 10*mm))
        story.append(Paragraph(f'<b>Notes:</b> {invoice.notes}', styles['Normal']))
    if invoice.terms:
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph(f'<b>Terms:</b> {invoice.terms}', styles['Normal']))

    doc.build(story)
    return buffer.getvalue()
