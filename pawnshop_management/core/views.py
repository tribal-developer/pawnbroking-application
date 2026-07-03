from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Sum

from .models import MetalRate
from loans.models import Loan
from customers.models import Customer


@login_required
def dashboard(request):
    """
    Landing page for staff: at-a-glance numbers on active loans, money out
    on the street, overdue accounts, and today's collections.
    """
    today = timezone.localdate()

    active_loans = Loan.objects.filter(status__in=['ACTIVE', 'OVERDUE'])
    overdue_loans = [loan for loan in active_loans if loan.is_overdue()]

    total_disbursed = active_loans.aggregate(total=Sum('principal_amount'))['total'] or Decimal('0')
    total_outstanding = sum((loan.outstanding_balance for loan in active_loans), Decimal('0'))

    todays_collections = (
        Loan.objects.filter(repayments__payment_date=today)
        .distinct()
    )
    todays_collection_total = sum(
        (r.amount for loan in todays_collections for r in loan.repayments.filter(payment_date=today)),
        Decimal('0'),
    )

    context = {
        'active_loan_count': active_loans.count(),
        'overdue_loan_count': len(overdue_loans),
        'overdue_loans': sorted(overdue_loans, key=lambda l: l.due_date)[:10],
        'total_disbursed': total_disbursed,
        'total_outstanding': total_outstanding,
        'todays_collection_total': todays_collection_total,
        'total_customers': Customer.objects.count(),
        'recent_loans': Loan.objects.order_by('-created_at')[:8],
        'current_gold_22k': MetalRate.get_current_rate('GOLD', '22K'),
        'current_silver': MetalRate.get_current_rate('SILVER', 'STERLING'),
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def metal_rate_list(request):
    rates = MetalRate.objects.all()[:30]
    return render(request, 'core/metal_rate_list.html', {'rates': rates})


@login_required
def metal_rate_create(request):
    from django import forms

    class MetalRateForm(forms.ModelForm):
        class Meta:
            model = MetalRate
            fields = ['metal', 'purity', 'rate_per_gram', 'effective_date']
            widgets = {'effective_date': forms.DateInput(attrs={'type': 'date'})}

    if request.method == 'POST':
        form = MetalRateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Metal rate updated.")
            return redirect('core:metal_rate_list')
    else:
        form = MetalRateForm(initial={'effective_date': timezone.localdate()})
    return render(request, 'core/metal_rate_form.html', {'form': form})
