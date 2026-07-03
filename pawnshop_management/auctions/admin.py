from django.contrib import admin
from .models import Auction


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('loan', 'auction_date', 'sale_amount', 'buyer_name', 'surplus_to_customer')
    search_fields = ('loan__loan_number', 'buyer_name')
