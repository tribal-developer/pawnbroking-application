from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from customers.models import Customer
from items.models import PledgeItem, ItemPhoto
from .forms import PledgeItemForm, LoanForm, RepaymentForm, RenewLoanForm
from .models import Loan


@login_required
def loan_create(request, customer_id):
    """
    Creates a PledgeItem and its Loan together in a single screen --
    this is the "new pledge" workflow staff use at the counter.
    """
    customer = get_object_or_404(Customer, pk=customer_id)

    if request.method == 'POST':
        item_form = PledgeItemForm(request.POST)
        loan_form = LoanForm(request.POST)
        if item_form.is_valid() and loan_form.is_valid():
            item = item_form.save(commit=False)
            item.customer = customer
            item.save()

            for photo_file in request.FILES.getlist('photos'):
                ItemPhoto.objects.create(item=item, image=photo_file)

            loan = loan_form.save(commit=False)
            loan.customer = customer
            loan.item = item
            loan.save()

            messages.success(request, f"Loan {loan.loan_number} created for {customer.full_name}.")
            return redirect('loans:detail', pk=loan.pk)
    else:
        item_form = PledgeItemForm()
        loan_form = LoanForm(initial={'issue_date': timezone.localdate()})

    return render(request, 'loans/loan_create.html', {
        'customer': customer,
        'item_form': item_form,
        'loan_form': loan_form,
    })


@login_required
def loan_list(request):
    status_filter = request.GET.get('status', 'open')  # open | overdue | closed | all
    loans = Loan.objects.select_related('customer', 'item')

    # Keep statuses fresh before filtering/displaying
    for loan in loans.filter(status='ACTIVE'):
        loan.refresh_status()

    if status_filter == 'open':
        loans = loans.filter(status__in=['ACTIVE', 'OVERDUE'])
    elif status_filter == 'overdue':
        loans = loans.filter(status='OVERDUE')
    elif status_filter == 'closed':
        loans = loans.filter(status__in=['REDEEMED', 'AUCTIONED'])
    # 'all' -> no filter

    return render(request, 'loans/loan_list.html', {'loans': loans, 'status_filter': status_filter})


@login_required
def loan_detail(request, pk):
    loan = get_object_or_404(Loan.objects.select_related('customer', 'item'), pk=pk)
    loan.refresh_status()
    repayments = loan.repayments.all()
    return render(request, 'loans/loan_detail.html', {
        'loan': loan,
        'repayments': repayments,
        'accrued_interest': loan.accrued_interest(),
        'outstanding_principal': loan.outstanding_principal,
        'outstanding_balance': loan.outstanding_balance,
    })


@login_required
def record_repayment(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    accrued_interest = loan.accrued_interest()
    outstanding_principal = loan.outstanding_principal
    outstanding_balance = loan.outstanding_balance

    if request.method == 'POST':
        form = RepaymentForm(request.POST)
        if form.is_valid():
            repayment = form.save(commit=False)

            # Full redemption always clears the loan exactly, regardless of
            # what staff typed -- avoids leaving a stray paisa of "balance".
            if repayment.payment_type == 'FULL_REDEMPTION':
                repayment.interest_component = accrued_interest
                repayment.principal_component = outstanding_principal
                repayment.amount = accrued_interest + outstanding_principal

            repayment.loan = loan
            repayment.recorded_by = request.user
            repayment.save()

            # Re-check whether this payment closes the loan out
            if loan.outstanding_balance <= 0 or repayment.payment_type == 'FULL_REDEMPTION':
                loan.status = 'REDEEMED'
                loan.closed_date = timezone.localdate()
                loan.save(update_fields=['status', 'closed_date'])
                loan.item.status = 'REDEEMED'
                loan.item.save(update_fields=['status'])
                messages.success(request, f"Loan {loan.loan_number} fully redeemed. Receipt: {repayment.receipt_number}")
            else:
                loan.status = 'ACTIVE'
                loan.save(update_fields=['status'])
                messages.success(request, f"Payment recorded. Receipt: {repayment.receipt_number}")

            return redirect('loans:detail', pk=loan.pk)
    else:
        # Pre-fill sensible defaults based on a quick-action link, e.g. ?type=interest_only
        quick_type = request.GET.get('type')
        if quick_type == 'interest_only':
            initial = {'payment_type': 'INTEREST_ONLY', 'amount': accrued_interest, 'interest_component': accrued_interest, 'principal_component': 0}
        elif quick_type == 'full':
            initial = {'payment_type': 'FULL_REDEMPTION', 'amount': outstanding_balance, 'interest_component': accrued_interest, 'principal_component': outstanding_principal}
        else:
            initial = {}
        initial['payment_date'] = timezone.localdate()
        form = RepaymentForm(initial=initial)

    return render(request, 'loans/repayment_form.html', {
        'loan': loan,
        'form': form,
        'accrued_interest': accrued_interest,
        'outstanding_principal': outstanding_principal,
        'outstanding_balance': outstanding_balance,
    })


@login_required
def renew_loan(request, pk):
    """
    Renewal = customer settles the accrued interest, then the due date is
    pushed out. Use this when a customer can't redeem yet but wants to keep
    the loan active instead of going overdue / to auction.
    """
    loan = get_object_or_404(Loan, pk=pk)
    accrued_interest = loan.accrued_interest()

    if request.method == 'POST':
        form = RenewLoanForm(request.POST)
        if form.is_valid():
            if accrued_interest > 0:
                from .models import Repayment
                Repayment.objects.create(
                    loan=loan,
                    payment_date=timezone.localdate(),
                    payment_type='INTEREST_ONLY',
                    amount=accrued_interest,
                    interest_component=accrued_interest,
                    principal_component=Decimal('0'),
                    recorded_by=request.user,
                )
            loan.renew(additional_months=form.cleaned_data['additional_months'])
            messages.success(request, f"Loan {loan.loan_number} renewed. New due date: {loan.due_date}.")
            return redirect('loans:detail', pk=loan.pk)
    else:
        form = RenewLoanForm()

    return render(request, 'loans/renew_form.html', {
        'loan': loan,
        'form': form,
        'accrued_interest': accrued_interest,
    })
