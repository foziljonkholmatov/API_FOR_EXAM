from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_('user')
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'carts'
        verbose_name = _('cart')
        verbose_name_plural = _('carts')

    def __str__(self):
        return f'Cart of {self.user.username}'

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def items_count(self):
        return self.items.count()

    def clear(self):
        self.items.all().delete()


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('product')
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name=_('product')
    )
    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=1,
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField(_('added at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'cart_items'
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        unique_together = ['cart', 'product']
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['cart', 'product']),
        ]

    def __str__(self):
        return f'{self.quantity} * {self.product.name}'

    @property
    def subtotal(self):
        return self.product.final_price() * self.quantity

    @property
    def is_available(self):
        return (
            self.product.is_active and
            self.product.is_in_stock and
            self.product.stock >= self.quantity
        )

    def can_increase_quantity(self, amount=1):
        return self.quantity + amount <= self.product.stock
