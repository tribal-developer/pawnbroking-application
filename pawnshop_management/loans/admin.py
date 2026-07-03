from django.contrib import admin
from .models import Loan, Repayment


class RepaymentInline(admin.TabularInline):
    model = Repayment
    extra = 0
    readonly_fields = ('receipt_number', 'created_at')


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        'loan_number', 'customer', 'item', 'principal_amount',
        'interest_rate_percent', 'issue_date', 'due_date', 'status',
    )
    list_filter = ('status', 'interest_type')
    search_fields = ('loan_number', 'customer__full_name')
    readonly_fields = ('loan_number', 'due_date')
    inlines = [RepaymentInline]


@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'loan', 'payment_date', 'payment_type', 'amount')
    list_filter = ('payment_type',)
    readonly_fields = ('receipt_number',)
