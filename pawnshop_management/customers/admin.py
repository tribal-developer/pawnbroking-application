from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'id_proof_type', 'id_proof_number', 'active_loans_count', 'date_registered')
    search_fields = ('full_name', 'phone_number', 'id_proof_number', 'email')
    list_filter = ('id_proof_type',)
