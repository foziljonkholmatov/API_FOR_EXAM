from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_image',
            'quantity', 'price', 'subtotal', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OrderListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'status_display', 'total_amount',
            'items_count', 'created_at', 'updated_at'
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    is_cancellable = serializers.BooleanField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'status', 'status_display', 'total_amount',
            'shipping_address', 'phone', 'notes',
            'items', 'items_count', 'is_cancellable',
            'created_at', 'updated_at',
            'processing_at', 'shipped_at', 'delivered_at', 'cancelled_at'
        ]
        read_only_fields = [
            'id', 'user', 'total_amount', 'created_at', 'updated_at',
            'processing_at', 'shipped_at', 'delivered_at', 'cancelled_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['shipping_address', 'phone', 'notes']

    def validate(self, attrs):
        if not attrs.get('shipping_address'):
            raise serializers.ValidationError({
                'shipping_address': _('Shipping address is required.')
            })

        if not attrs.get('phone'):
            raise serializers.ValidationError({
                'phone': _('Phone number is required.')
            })

        return attrs


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

    def validate_status(self, value):
        order = self.instance
        current_status = order.status
        valid_transitions = {
            Order.OrderStatus.PENDING: [
                Order.OrderStatus.PROCESSING,
                Order.OrderStatus.CANCELLED
            ],
            Order.OrderStatus.PROCESSING: [
                Order.OrderStatus.SHIPPED,
                Order.OrderStatus.CANCELLED
            ],
            Order.OrderStatus.SHIPPED: [
                Order.OrderStatus.DELIVERED
            ],
            Order.OrderStatus.DELIVERED: [],
            Order.OrderStatus.CANCELLED: [],
        }

        if value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                _(f'Cannot change status from {current_status} to {value}.')
            )

        return value


class OrderCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        order = self.context.get('order')

        if not order.is_cancellable:
            raise serializers.ValidationError(
                _('This order cannot be cancelled.')
            )

        return attrs
