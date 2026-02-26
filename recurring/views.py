from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from organizations.models import Organization, OrganizationMembership
from clients.models import Client
from invoices.models import Invoice
from .models import RecurringInvoice


def _get_org(request):
    m = OrganizationMembership.objects.filter(user=request.user).select_related('organization').first()
    return m.organization if m else None


class RecurringForm(forms.ModelForm):
    class Meta:
        model = RecurringInvoice
        fields = ['template_invoice', 'frequency', 'start_date', 'end_date',
                  'max_occurrences', 'next_run_date', 'is_active']
        widgets = {
            'template_invoice': forms.Select(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_run_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'max_occurrences': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank for unlimited'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, org=None, **kwargs):
        super().__init__(*args, **kwargs)
        if org:
            self.fields['template_invoice'].queryset = Invoice.objects.filter(
                organization=org, status=Invoice.STATUS_DRAFT
            )


@login_required
def recurring_list(request):
    org = _get_org(request)
    if not org:
        return redirect('organizations:onboarding')
    schedules = RecurringInvoice.objects.filter(organization=org).select_related(
        'template_invoice', 'template_invoice__client'
    )
    return render(request, 'recurring/list.html', {'schedules': schedules, 'org': org})


@login_required
def recurring_create(request):
    org = _get_org(request)
    if not org:
        return redirect('organizations:onboarding')
    form = RecurringForm(org=org)
    if request.method == 'POST':
        form = RecurringForm(request.POST, org=org)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.organization = org
            schedule.save()
            messages.success(request, 'Recurring schedule created.')
            return redirect('recurring:list')
    return render(request, 'recurring/form.html', {'form': form, 'org': org, 'title': 'New Recurring Invoice'})


@login_required
def recurring_toggle(request, pk):
    org = _get_org(request)
    schedule = get_object_or_404(RecurringInvoice, pk=pk, organization=org)
    schedule.is_active = not schedule.is_active
    schedule.save()
    status = 'activated' if schedule.is_active else 'paused'
    messages.success(request, f'Schedule {status}.')
    return redirect('recurring:list')


@login_required
def recurring_delete(request, pk):
    org = _get_org(request)
    schedule = get_object_or_404(RecurringInvoice, pk=pk, organization=org)
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Recurring schedule deleted.')
        return redirect('recurring:list')
    return render(request, 'recurring/confirm_delete.html', {'schedule': schedule, 'org': org})
