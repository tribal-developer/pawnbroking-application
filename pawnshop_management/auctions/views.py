from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from loans.models import Loan
from .models import Auction


class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['auction_date', 'sale_amount', 'buyer_name', 'notes']
        widgets = {
            'auction_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


@login_required
def auction_eligible_list(request):
    """Loans overdue long enough (per AUCTION_GRACE_PERIOD_DAYS) to forfeit."""
    candidates = [
        loan for loan in Loan.objects.filter(status__in=['ACTIVE', 'OVERDUE']).select_related('customer', 'item')
        if loan.is_eligible_for_auction()
    ]
    return render(request, 'auctions/auction_eligible_list.html', {'loans': candidates})


@login_required
def auction_list(request):
    auctions = Auction.objects.select_related('loan', 'loan__customer')
    return render(request, 'auctions/auction_list.html', {'auctions': auctions})


@login_required
def auction_create(request, loan_id):
    loan = get_object_or_404(Loan, pk=loan_id)

    if request.method == 'POST':
        form = AuctionForm(request.POST)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.loan = loan
            auction.save()

            loan.status = 'AUCTIONED'
            loan.closed_date = timezone.localdate()
            loan.save(update_fields=['status', 'closed_date'])
            loan.item.status = 'AUCTIONED'
            loan.item.save(update_fields=['status'])

            if auction.surplus_to_customer > 0:
                messages.warning(
                    request,
                    f"Auction recorded. Surplus of ₹{auction.surplus_to_customer} is owed back to "
                    f"{loan.customer.full_name} -- many jurisdictions require this to be returned.",
                )
            else:
                messages.success(request, "Auction recorded and loan closed.")
            return redirect('auctions:list')
    else:
        form = AuctionForm(initial={'auction_date': timezone.localdate()})

    return render(request, 'auctions/auction_create.html', {
        'loan': loan,
        'form': form,
        'amount_owed': loan.outstanding_balance,
    })
