"""
Seeds the database with a sample staff user, metal rates, customers, items,
and loans so you can explore the app immediately after setup.

Usage:
    python manage.py seed_demo_data
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import MetalRate
from customers.models import Customer
from items.models import PledgeItem
from loans.models import Loan


class Command(BaseCommand):
    help = "Seed the database with demo data (staff user, customers, items, loans)."

    def handle(self, *args, **options):
        today = timezone.localdate()

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS("Created superuser 'admin' / password 'admin123' -- change this immediately."))
        else:
            self.stdout.write("Superuser 'admin' already exists, skipping.")

        MetalRate.objects.get_or_create(metal='GOLD', purity='22K', effective_date=today, defaults={'rate_per_gram': 6200})
        MetalRate.objects.get_or_create(metal='GOLD', purity='18K', effective_date=today, defaults={'rate_per_gram': 5100})
        MetalRate.objects.get_or_create(metal='SILVER', purity='STERLING', effective_date=today, defaults={'rate_per_gram': 85})
        self.stdout.write(self.style.SUCCESS("Seeded today's metal rates."))

        demo_customers = [
            {
                'full_name': 'Rohit Sharma', 'phone_number': '9876543210',
                'address': '12 MG Road, Betul, MP', 'id_proof_type': 'AADHAAR', 'id_proof_number': '1234-5678-9012',
            },
            {
                'full_name': 'Priya Verma', 'phone_number': '9876501234',
                'address': '45 Station Road, Betul, MP', 'id_proof_type': 'PAN', 'id_proof_number': 'ABCDE1234F',
            },
        ]
        customers = []
        for data in demo_customers:
            customer, created = Customer.objects.get_or_create(phone_number=data['phone_number'], defaults=data)
            customers.append(customer)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(customers)} demo customers."))

        if not Loan.objects.exists():
            # Loan 1: a healthy, current loan
            item1 = PledgeItem.objects.create(
                customer=customers[0], item_type='RING', description='Gold ring with red stone',
                metal='GOLD', purity='22K', gross_weight_grams=8.5, stone_weight_grams=0.5,
                appraised_value=48000,
            )
            Loan.objects.create(
                customer=customers[0], item=item1, principal_amount=35000,
                interest_rate_percent=2.0, issue_date=today - timedelta(days=20), tenure_months=3,
            )

            # Loan 2: overdue, eligible to demonstrate the overdue/auction flow
            item2 = PledgeItem.objects.create(
                customer=customers[1], item_type='CHAIN', description='Gold chain, machine-made',
                metal='GOLD', purity='22K', gross_weight_grams=15.0, stone_weight_grams=0,
                appraised_value=84000,
            )
            overdue_loan = Loan.objects.create(
                customer=customers[1], item=item2, principal_amount=60000,
                interest_rate_percent=2.5, issue_date=today - timedelta(days=130), tenure_months=3,
            )
            overdue_loan.refresh_status()

            self.stdout.write(self.style.SUCCESS("Seeded 2 demo loans (1 current, 1 overdue)."))
        else:
            self.stdout.write("Loans already exist, skipping loan seed.")

        self.stdout.write(self.style.SUCCESS("Demo data ready. Log in with admin / admin123."))
