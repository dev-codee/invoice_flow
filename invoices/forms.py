from django import forms
from .models import Invoice, InvoiceLineItem
from clients.models import Client


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client', 'issue_date', 'due_date', 'notes', 'terms', 'discount_amount']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Payment notes visible to client…'}),
            'terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Terms & conditions…'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

    def __init__(self, organization=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['client'].queryset = Client.objects.filter(
                organization=organization, is_active=True
            )


class LineItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceLineItem
        fields = ['description', 'quantity', 'unit_price', 'tax_rate', 'discount']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Service description'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
        }


LineItemFormSet = forms.inlineformset_factory(
    Invoice, InvoiceLineItem,
    form=LineItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
