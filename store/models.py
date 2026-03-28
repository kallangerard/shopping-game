from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Item(models.Model):
    THUMBNAIL_EMOJI = 'emoji'
    THUMBNAIL_IMAGE = 'image'
    THUMBNAIL_CHOICES = [
        (THUMBNAIL_EMOJI, 'Emoji'),
        (THUMBNAIL_IMAGE, 'Image'),
    ]

    name = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    thumbnail_type = models.CharField(
        max_length=10,
        choices=THUMBNAIL_CHOICES,
        default=THUMBNAIL_EMOJI,
    )
    emoji = models.CharField(
        max_length=10,
        blank=True,
        default='🛒',
        help_text='Emoji character to use as thumbnail',
    )
    image = models.ImageField(
        upload_to='items/',
        blank=True,
        null=True,
        help_text='Image to use as thumbnail',
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (${self.price})'

    @property
    def thumbnail_display(self):
        if self.thumbnail_type == self.THUMBNAIL_IMAGE and self.image:
            return ('image', self.image.url)
        return ('emoji', self.emoji or '🛒')


class Transaction(models.Model):
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    amount_given = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    change = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Transaction #{self.pk} – ${self.total} (paid ${self.amount_given}, change ${self.change})'

    def calculate_change(self):
        self.change = self.amount_given - self.total
        return self.change


class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f'{self.quantity}x {self.item.name} @ ${self.unit_price}'

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
