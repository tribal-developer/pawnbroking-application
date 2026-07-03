from decimal import Decimal

from django.db import models


class Customer(models.Model):
    """A person who pledges jewelry/items in exchange for a loan."""

    ID_PROOF_CHOICES = [
        ('AADHAAR', 'Aadhaar Card'),
        ('PAN', 'PAN Card'),
        ('PASSPORT', 'Passport'),
        ('VOTER_ID', 'Voter ID'),
        ('DRIVING_LICENSE', 'Driving License'),
        ('OTHER', 'Other Government ID'),
    ]

    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField()
    photo = models.ImageField(upload_to='customers/photos/', blank=True, null=True)

    id_proof_type = models.CharField(max_length=20, choices=ID_PROOF_CHOICES)
    id_proof_number = models.CharField(max_length=50)
    id_proof_document = models.FileField(upload_to='customers/id_proofs/', blank=True, null=True)

    date_registered = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Internal staff notes about this customer")

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"

    @property
    def active_loans(self):
        return self.loans.filter(status__in=['ACTIVE', 'OVERDUE'])

    @property
    def active_loans_count(self):
        return self.active_loans.count()

    @property
    def total_outstanding(self):
        return sum((loan.outstanding_balance for loan in self.active_loans), Decimal('0'))

    @property
    def total_loans_count(self):
        return self.loans.count()
