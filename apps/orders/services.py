from typing import Dict, List
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderItem
from ..cart.services import CartService


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(user, validated_data: dict) -> Order:
        cart = CartService.get_or_create_cart(user)

        if not cart.items.exists():
            raise ValidationError(_('Cart is empty.'))

        validation = CartService.validate_cart_items(cart)
        if not validation['is_valid']:
            raise ValidationError({
                'cart': _('Some items in cart are not available.'),
                'invalid_items': validation['invalid_items']
            })

        order = Order.objects.create(
            user=user,
            total_amount=cart.total_price,
            shipping_address=validated_data['shipping_address'],
            phone=validated_data['phone'],
            notes=validated_data.get('notes', '')
        )

        order_items = []
        for cart_item in cart.items.select_related('product').all():
            order_item = OrderItem(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_image=cart_item.product.image,
                quantity=cart_item.quantity,
                price=cart_item.product.final_price
            )
            order_items.append(order_item)

            cart_item.product.stock -= cart_item.quantity
            cart_item.product.save(update_fields=['stock'])

        OrderItem.objects.bulk_create(order_items)

        CartService.clear_cart(cart)

        return order

    @staticmethod
    @transaction.atomic
    def update_order_status(order: Order, new_status: str) -> Order:
        old_status = order.status
        order.status = new_status

        now = timezone.now()

        if new_status == Order.OrderStatus.PROCESSING:
            order.processing_at = now
        elif new_status == Order.OrderStatus.SHIPPED:
            order.shipped_at = now
        elif new_status == Order.OrderStatus.DELIVERED:
            order.delivered_at = now
        elif new_status == Order.OrderStatus.CANCELLED:
            order.cancelled_at = now

        order.save()

        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(order: Order, reason: str = None) -> Order:
        if not order.is_cancellable:
            raise ValidationError(_('This order cannot be cancelled.'))
        for item in order.items.select_related('product').all():
            item.product.stock += item.quantity
            item.product.save(update_fields=['stock'])
        order.status = Order.OrderStatus.CANCELLED
        order.cancelled_at = timezone.now()

        if reason:
            order.notes = f"{order.notes}\n\nCancellation reason: {reason}".strip()

        order.save()

        return order

    @staticmethod
    def get_user_orders(user, status: str = None) -> List[Order]:
        orders = Order.objects.filter(user=user).select_related('user').prefetch_related('items')

        if status:
            orders = orders.filter(status=status)

        return orders

    @staticmethod
    def get_order_statistics(order: Order) -> Dict:
        items = order.items.all()

        return {
            'total_items': sum(item.quantity for item in items),
            'unique_items': items.count(),
            'average_item_price': order.total_amount / sum(item.quantity for item in items) if items else 0,
        }

    @staticmethod
    def get_user_order_statistics(user) -> Dict:
        orders = Order.objects.filter(user=user)

        return {
            'total_orders': orders.count(),
            'pending_orders': orders.filter(status=Order.OrderStatus.PENDING).count(),
            'completed_orders': orders.filter(status=Order.OrderStatus.DELIVERED).count(),
            'cancelled_orders': orders.filter(status=Order.OrderStatus.CANCELLED).count(),
            'total_spent': sum(order.total_amount for order in orders.exclude(status=Order.OrderStatus.CANCELLED)),
        }
