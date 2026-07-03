from django.contrib import admin
from .models import PledgeItem, ItemPhoto


class ItemPhotoInline(admin.TabularInline):
    model = ItemPhoto
    extra = 1


@admin.register(PledgeItem)
class PledgeItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'item_type', 'metal', 'purity', 'net_weight_grams', 'appraised_value', 'status')
    list_filter = ('item_type', 'metal', 'purity', 'status')
    search_fields = ('customer__full_name', 'description')
    inlines = [ItemPhotoInline]
