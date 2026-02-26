from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'billing_address', 'currency', 'tax_id', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Client name or company'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'client@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 555 000 0000'}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'currency': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('USD', 'USD — US Dollar'), ('EUR', 'EUR — Euro'), ('GBP', 'GBP — British Pound'),
                ('CAD', 'CAD — Canadian Dollar'), ('AUD', 'AUD — Australian Dollar'),
                ('INR', 'INR — Indian Rupee'), ('PKR', 'PKR — Pakistani Rupee'),
            ]),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VAT / Tax ID (optional)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Internal notes (not shown on invoices)'}),
        }
