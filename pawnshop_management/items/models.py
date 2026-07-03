from django.db import models

from customers.models import Customer


class PledgeItem(models.Model):
    """A single piece of jewelry (or other valuable) pledged as collateral."""

    ITEM_TYPE_CHOICES = [
        ('RING', 'Ring'),
        ('NECKLACE', 'Necklace'),
        ('CHAIN', 'Chain'),
        ('BANGLE', 'Bangle'),
        ('BRACELET', 'Bracelet'),
        ('EARRINGS', 'Earrings'),
        ('PENDANT', 'Pendant'),
        ('COIN_BAR', 'Coin / Bar'),
        ('WATCH', 'Watch'),
        ('OTHER', 'Other'),
    ]
    METAL_CHOICES = [
        ('GOLD', 'Gold'),
        ('SILVER', 'Silver'),
        ('PLATINUM', 'Platinum'),
        ('OTHER', 'Other / Mixed'),
    ]
    PURITY_CHOICES = [
        ('24K', '24 Karat (999)'),
        ('22K', '22 Karat (916)'),
        ('18K', '18 Karat (750)'),
        ('14K', '14 Karat (585)'),
        ('STERLING', 'Sterling Silver (92.5%)'),
        ('FINE_SILVER', 'Fine Silver (99.9%)'),
        ('NA', 'Not Applicable'),
    ]
    STATUS_CHOICES = [
        ('PLEDGED', 'Pledged (loan active)'),
        ('REDEEMED', 'Redeemed (returned to customer)'),
        ('AUCTIONED', 'Auctioned'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    description = models.CharField(
        max_length=255,
        help_text="e.g. 'Floral design gold ring with red stone, slightly worn'",
    )
    metal = models.CharField(max_length=10, choices=METAL_CHOICES)
    purity = models.CharField(max_length=15, choices=PURITY_CHOICES)

    gross_weight_grams = models.DecimalField(max_digits=8, decimal_places=3)
    stone_weight_grams = models.DecimalField(
        max_digits=8, decimal_places=3, default=0,
        help_text="Weight of non-metal stones/gems to deduct from gross weight",
    )
    net_weight_grams = models.DecimalField(max_digits=8, decimal_places=3, editable=False)

    appraised_value = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Value assigned by staff at appraisal time (can be auto-suggested from the daily metal rate, then overridden)",
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLEDGED')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.net_weight_grams = (self.gross_weight_grams or 0) - (self.stone_weight_grams or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_item_type_display()} - {self.net_weight_grams}g {self.purity} ({self.customer.full_name})"


class ItemPhoto(models.Model):
    """Photographic evidence of an item's condition at pledge time."""
    item = models.ForeignKey(PledgeItem, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='items/photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo of {self.item}"
