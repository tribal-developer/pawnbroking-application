from django import forms

from items.models import PledgeItem
from .models import Loan, Repayment


class PledgeItemForm(forms.ModelForm):
    class Meta:
        model = PledgeItem
        fields = [
            'item_type', 'description', 'metal', 'purity',
            'gross_weight_grams', 'stone_weight_grams', 'appraised_value',
        ]
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': "e.g. Floral design gold ring with red stone"}),
        }


class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['principal_amount', 'interest_rate_percent', 'interest_type', 'issue_date', 'tenure_months']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
        }


class RepaymentForm(forms.ModelForm):
    class Meta:
        model = Repayment
        fields = ['payment_date', 'payment_type', 'amount', 'interest_component', 'principal_component']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }


class RenewLoanForm(forms.Form):
    additional_months = forms.IntegerField(min_value=1, initial=1, label="Extend tenure by (months)")
