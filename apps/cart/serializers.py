from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.cart.models import CartItem, Cart
from apps.products.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField( read_only=True)
    product_name = serializers.CharField(read_only=True)
    product_slug = serializers.CharField(read_only=True)
    product_image = serializers.ImageField(read_only=True)
    product_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    final_price = serializers.DecimalField(
        source='product.final_price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    subtotal = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id', 'product_id', 'product_name', 'product_slug',
            'product_image', 'product_price', 'final_price',
            'quantity', 'subtotal', 'is_available',
            'added_at', 'updated_at'
        ]
        read_only_fields = ['id', 'added_at', 'updated_at']


class CartItemCreateSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True)
    )

    class Meta:
        model = CartItem
        fields = ['product', 'quantity']

    def validate_product(self, value):
        if not value.is_active:
            raise serializers.ValidationError(_('This product is not available. '))
        if not value.is_in_stock:
            raise serializers.ValidationError(_('This product is out of stock. '))
        return value

    def validate(self, attrs):
        product = attrs.get('product')
        quantity = attrs.get('quantity', 1)

        if quantity > product.stock:
            raise serializers.ValidationError({
                'quantity': _(f'Only {product.stock} items available in stock')
            })
        cart = self.context.get('cart')
        if cart:
            try:
                existing_item = CartItem.objects.get(cart=cart, product=product)
                new_quantity = existing_item.quantity + quantity

                if new_quantity > product.stock:
                    raise serializers.ValidationError({
                        'quantity': _(f'Cannot add more. Only {product.stock} items available.')
                    })
            except CartItem.DoesNotExist:
                pass
        return attrs


class CartItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(_('Quantity must be at least 1 .'))
        product = self.instance.product

        if value > product.stock:
            raise serializers.ValidationError(
                _(f'Only {product.stock} items available in stock.')
            )
        return value

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    total_items = serializers.IntegerField(read_only=True)
    items_total = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields =[
            'id', 'user', 'items', 'total_price',
            'total_items', 'items_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

