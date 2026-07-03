from decimal import Decimal

from django.db import models

from loans.models import Loan


class Auction(models.Model):
    """
    Records the forfeiture/sale of an item whose loan was never redeemed.
    Many regions legally require any surplus (sale price minus what was
    owed) to be returned to the customer -- surplus_to_customer makes that
    number explicit so staff can act on it.
    """

    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name='auction')
    auction_date = models.DateField()
    sale_amount = models.DecimalField(max_digits=12, decimal_places=2)
    buyer_name = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-auction_date']

    def __str__(self):
        return f"Auction - {self.loan.loan_number}"

    @property
    def amount_owed_at_auction(self):
        return self.loan.outstanding_balance

    @property
    def surplus_to_customer(self):
        surplus = self.sale_amount - self.amount_owed_at_auction
        return surplus if surplus > 0 else Decimal('0')

    @property
    def shortfall(self):
        shortfall = self.amount_owed_at_auction - self.sale_amount
        return shortfall if shortfall > 0 else Decimal('0')
