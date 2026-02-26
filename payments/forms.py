from django import forms
from .models import Payment
from django.utils import timezone


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_date', 'method', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes…'}),
        }

    def __init__(self, invoice=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if invoice:
            self.fields['amount'].initial = invoice.balance_due
        self.fields['payment_date'].initial = timezone.now().date()
