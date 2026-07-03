"""
Loan models and interest calculation.

BUSINESS RULE NOTE: Pawnbroker interest rules vary a lot by region (and are
often legally capped). The calculation here implements a common, simple
approach:

  - Interest is quoted as a MONTHLY percentage rate (e.g. 2.5% / month).
  - A partial month is billed as a full month, controlled by
    settings.ROUND_UP_PARTIAL_MONTH_INTEREST (this matches common
    pawnbroker practice -- a loan taken on day 1 and repaid on day 35 is
    usually billed 2 months, not ~1.16 months).
  - "FLAT_MONTHLY" charges interest on the original principal every month.
  - "REDUCING" charges interest on the currently outstanding principal.

Adjust accrued_interest() if your shop uses a different policy (e.g. daily
interest, slab-based rates, or a legally mandated minimum/maximum).
"""

import calendar
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from customers.models import Customer
from items.models import PledgeItem


def add_months(start_date, months):
    """Return start_date + N months, clamping the day to a valid date."""
    month_index = start_date.month - 1 + months
    year = start_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start_date.day, calendar.monthrange(year, month)[1])
    return start_date.replace(year=year, month=month, day=day)


def months_elapsed(start_date, end_date, round_up_partial=True):
    """
    Number of whole months between two dates, for interest billing purposes.
    If round_up_partial is True, any leftover days count as one more month
    (and a brand-new loan starts owing 1 month's interest immediately, which
    matches how most pawnbrokers price a part-month).
    """
    if end_date <= start_date:
        return 0

    full_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if end_date.day < start_date.day:
        full_months -= 1
    full_months = max(full_months, 0)

    anchor = add_months(start_date, full_months)
    has_remainder = end_date > anchor

    if round_up_partial and (has_remainder or full_months == 0):
        full_months += 1

    return full_months


class Loan(models.Model):
    """A loan issued against a single pledged item."""

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('OVERDUE', 'Overdue'),
        ('REDEEMED', 'Redeemed'),
        ('AUCTIONED', 'Auctioned / Closed'),
    ]
    INTEREST_TYPE_CHOICES = [
        ('FLAT_MONTHLY', 'Flat (on original principal)'),
        ('REDUCING', 'Reducing balance (on outstanding principal)'),
    ]

    loan_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='loans')
    item = models.OneToOneField(PledgeItem, on_delete=models.CASCADE, related_name='loan')

    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate_percent = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Monthly interest rate, e.g. 2.5 for 2.5% per month",
    )
    interest_type = models.CharField(max_length=20, choices=INTEREST_TYPE_CHOICES, default='FLAT_MONTHLY')

    issue_date = models.DateField(default=timezone.localdate)
    tenure_months = models.PositiveIntegerField(default=3)
    due_date = models.DateField(editable=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    closed_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not self.loan_number:
            self.loan_number = self._generate_loan_number()
        if is_new or not self.due_date:
            self.due_date = add_months(self.issue_date, self.tenure_months)
        super().save(*args, **kwargs)

    def _generate_loan_number(self):
        year = timezone.localdate().year
        count = Loan.objects.filter(created_at__year=year).count() + 1
        return f"LN-{year}-{count:05d}"

    def __str__(self):
        return self.loan_number

    # --- Money math ---------------------------------------------------

    @property
    def total_repaid(self):
        return self.repayments.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    @property
    def total_interest_paid(self):
        return self.repayments.aggregate(total=Sum('interest_component'))['total'] or Decimal('0')

    @property
    def total_principal_paid(self):
        return self.repayments.aggregate(total=Sum('principal_component'))['total'] or Decimal('0')

    @property
    def outstanding_principal(self):
        return self.principal_amount - self.total_principal_paid

    def accrued_interest(self, as_of_date=None):
        """Total interest owed as of a given date, minus what's already been paid."""
        as_of_date = as_of_date or timezone.localdate()
        round_up = getattr(settings, 'ROUND_UP_PARTIAL_MONTH_INTEREST', True)
        months = months_elapsed(self.issue_date, as_of_date, round_up_partial=round_up)

        rate = self.interest_rate_percent / Decimal('100')
        if self.interest_type == 'FLAT_MONTHLY':
            total_interest_due = self.principal_amount * rate * Decimal(months)
        else:  # REDUCING -- approximate using current outstanding principal
            total_interest_due = self.outstanding_principal * rate * Decimal(months)

        outstanding_interest = total_interest_due - self.total_interest_paid
        return max(outstanding_interest, Decimal('0'))

    @property
    def outstanding_balance(self):
        return self.outstanding_principal + self.accrued_interest()

    # --- Status helpers --------------------------------------------------

    def is_overdue(self):
        return self.status in ('ACTIVE', 'OVERDUE') and timezone.localdate() > self.due_date

    def is_eligible_for_auction(self):
        grace_days = getattr(settings, 'AUCTION_GRACE_PERIOD_DAYS', 30)
        if self.status not in ('ACTIVE', 'OVERDUE'):
            return False
        days_overdue = (timezone.localdate() - self.due_date).days
        return days_overdue >= grace_days

    def renew(self, additional_months=1):
        """Extend the due date -- used once accrued interest has been settled."""
        self.due_date = add_months(self.due_date, additional_months)
        self.tenure_months += additional_months
        self.status = 'ACTIVE'
        self.save()

    def refresh_status(self):
        """Flip ACTIVE -> OVERDUE automatically; call from a scheduled task or view."""
        if self.status == 'ACTIVE' and self.is_overdue():
            self.status = 'OVERDUE'
            self.save(update_fields=['status'])


class Repayment(models.Model):
    """A single payment made against a loan (interest, partial, or full redemption)."""

    PAYMENT_TYPE_CHOICES = [
        ('INTEREST_ONLY', 'Interest Only'),
        ('PARTIAL', 'Partial Payment (Principal + Interest)'),
        ('FULL_REDEMPTION', 'Full Redemption'),
    ]

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    payment_date = models.DateField(default=timezone.localdate)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_component = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    principal_component = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    receipt_number = models.CharField(max_length=20, unique=True, editable=False)
    recorded_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='repayments_recorded',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self._generate_receipt_number()
        super().save(*args, **kwargs)

    def _generate_receipt_number(self):
        year = timezone.localdate().year
        count = Repayment.objects.filter(created_at__year=year).count() + 1
        return f"RCT-{year}-{count:05d}"

    def __str__(self):
        return self.receipt_number
