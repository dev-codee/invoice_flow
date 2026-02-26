import csv
import io
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Client
from .forms import ClientForm


def get_org(request):
    m = request.user.memberships.select_related('organization').first()
    return m.organization if m else None


@login_required
def client_list(request):
    org = get_org(request)
    qs = Client.objects.filter(organization=org)
    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q))
    active_filter = request.GET.get('active', '')
    if active_filter == '1':
        qs = qs.filter(is_active=True)
    elif active_filter == '0':
        qs = qs.filter(is_active=False)
    return render(request, 'clients/list.html', {'clients': qs, 'q': q, 'org': org})


@login_required
def client_create(request):
    org = get_org(request)
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.organization = org
            client.save()
            messages.success(request, f'Client "{client.name}" created.')
            return redirect('clients:detail', pk=client.pk)
    else:
        form = ClientForm()
    return render(request, 'clients/form.html', {'form': form, 'title': 'New Client'})


@login_required
def client_detail(request, pk):
    org = get_org(request)
    client = get_object_or_404(Client, pk=pk, organization=org)
    invoices = client.invoices.order_by('-created_at')
    return render(request, 'clients/detail.html', {'client': client, 'invoices': invoices})


@login_required
def client_update(request, pk):
    org = get_org(request)
    client = get_object_or_404(Client, pk=pk, organization=org)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client updated.')
            return redirect('clients:detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'clients/form.html', {'form': form, 'title': f'Edit {client.name}', 'client': client})


@login_required
def client_delete(request, pk):
    org = get_org(request)
    client = get_object_or_404(Client, pk=pk, organization=org)
    if request.method == 'POST':
        name = client.name
        client.is_active = False
        client.save()
        messages.success(request, f'Client "{name}" deactivated.')
        return redirect('clients:list')
    return render(request, 'clients/confirm_delete.html', {'client': client})


@login_required
def client_import_csv(request):
    org = get_org(request)
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded = csv_file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        created = 0
        for row in reader:
            name = row.get('name', '').strip()
            email = row.get('email', '').strip()
            if name and email:
                Client.objects.get_or_create(
                    organization=org, email=email,
                    defaults={
                        'name': name,
                        'phone': row.get('phone', ''),
                        'billing_address': row.get('billing_address', ''),
                        'currency': row.get('currency', org.currency),
                    }
                )
                created += 1
        messages.success(request, f'Imported {created} clients.')
        return redirect('clients:list')
    return render(request, 'clients/import_csv.html')
