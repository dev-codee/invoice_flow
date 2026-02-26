from django import forms
from .models import Organization, OrganizationMembership, Invitation


class OrganizationSetupForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'slug', 'currency', 'tax_rate', 'payment_terms', 'address', 'phone', 'website', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Acme Corp'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'acme-corp', 'required': False}),
            'currency': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('USD', 'USD — US Dollar'), ('EUR', 'EUR — Euro'), ('GBP', 'GBP — British Pound'),
                ('CAD', 'CAD — Canadian Dollar'), ('AUD', 'AUD — Australian Dollar'),
                ('INR', 'INR — Indian Rupee'), ('PKR', 'PKR — Pakistani Rupee'),
            ]),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': False}),
            'payment_terms': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'required': False}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class InviteForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ['email', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'colleague@company.com'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
