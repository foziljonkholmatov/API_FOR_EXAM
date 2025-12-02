from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.cart.models import Cart, CartItem
from apps.products.models import Product


class CartService:
    @staticmethod
    def get_or_create_cart(user) -> Cart:
        cart, created = Cart.objects.get_or_create(user=user)
        return cart

    @staticmethod
    @transaction.atomic
    def add_to_cart(cart: Cart, product: Product, quantity: int = 1) -> CartItem:
        if not product.is_active:
            raise ValidationError(_('This product is not available. '))
        if not product.is_in_stock:
            raise ValidationError(_('This product is out of stock.'))

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            new_quantity = cart_item.quantity + quantity

            if new_quantity > product.stock:
                raise ValidationError(
                    _(f'Cannot add more. Only{product.stock} items available.')
                )
            cart_item.quantity = new_quantity
            cart_item.save(update_fields=['quantity', 'updated_at'])
        else:
            if quantity > product.stock:
                cart_item.delete()
                raise ValidationError(_(f'Only {product.stock} items available stock.'))
        return cart_item

    @staticmethod
    @transaction.atomic
    def update_cart_item(cart_item: CartItem, quantity: int) -> CartItem:
        if quantity < 1:
            raise ValidationError(_('Quantity must be last 1.'))
        if quantity > cart_item.product.stock:
            raise ValidationError(
                _(f'Only {cart_item.product.stock} items available in stock.')
            )
        cart_item.quantity = quantity
        cart_item.save(update_fields=['quantity', 'updated_at'])
        return cart_item

    @staticmethod
    @transaction.atomic
    def  remove_from_cart(cart_item: CartItem) -> None:
        cart_item.delete()

    @staticmethod
    @transaction.atomic
    def clear_cart(cart: Cart) -> None:
        cart.clear()


    @staticmethod
    def validate_cart_items(cart:Cart) -> dict:

        invalid_items = []
        valid_items = []

        for item in cart.items.select_related('product').all():
            if not item.is_available:
                invalid_items.append({
                    'item_id': item.id,
                    'product_name': item.product_name,
                    'reason': 'Product not available or out of stock'
                })
            elif item.quantity > item.product.stock:
                invalid_items.append({
                    'item_id': item.id,
                    'product_name': item.product.name,
                    'reason': f'Only {item.product.stock} items available.'
                })
            else:
                valid_items.append(item.id)
        return {
            'is_valid': len(invalid_items) == 0,
            'invalid_items': invalid_items,
            'valid_items': valid_items
        }
    @staticmethod
    def get_cart_summary(cart: Cart) -> dict:
        return {
            'total_price': cart.total_price,
            'total_items': cart.total_items,
            'items_count': cart.items_count,
        }


