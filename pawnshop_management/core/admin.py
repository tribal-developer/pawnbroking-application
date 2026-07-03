from django.contrib import admin
from .models import MetalRate


@admin.register(MetalRate)
class MetalRateAdmin(admin.ModelAdmin):
    list_display = ('metal', 'purity', 'rate_per_gram', 'effective_date')
    list_filter = ('metal', 'purity')
    ordering = ('-effective_date',)
