from django.db import models
from django.utils import timezone


class MetalRate(models.Model):
    """
    Daily gold/silver rate used to auto-suggest appraised values for pledged
    items. Staff should update this each business day.
    """
    METAL_CHOICES = [
        ('GOLD', 'Gold'),
        ('SILVER', 'Silver'),
    ]
    PURITY_CHOICES = [
        ('24K', '24 Karat (999)'),
        ('22K', '22 Karat (916)'),
        ('18K', '18 Karat (750)'),
        ('14K', '14 Karat (585)'),
        ('STERLING', 'Sterling Silver (92.5%)'),
        ('FINE_SILVER', 'Fine Silver (99.9%)'),
    ]

    metal = models.CharField(max_length=10, choices=METAL_CHOICES)
    purity = models.CharField(max_length=15, choices=PURITY_CHOICES)
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_date', 'metal']
        unique_together = ('metal', 'purity', 'effective_date')
        verbose_name = "Metal Rate"
        verbose_name_plural = "Metal Rates"

    def __str__(self):
        return f"{self.get_metal_display()} {self.purity} - {self.effective_date}: ₹{self.rate_per_gram}/g"

    @classmethod
    def get_current_rate(cls, metal, purity):
        """Most recent rate on or before today for this metal/purity combo."""
        return (
            cls.objects.filter(metal=metal, purity=purity, effective_date__lte=timezone.localdate())
            .order_by('-effective_date')
            .first()
        )
