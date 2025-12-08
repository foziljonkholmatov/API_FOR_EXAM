from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    CartItemCreateSerializer,
    CartItemUpdateSerializer,
)
from .services import CartService


@extend_schema(tags=['Cart'], summary='Get/Add to Cart', description='Get user cart or add product to cart')
class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = CartService.get_or_create_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @extend_schema(request=CartItemCreateSerializer)
    def post(self, request):
        cart = CartService.get_or_create_cart(request.user)

        serializer = CartItemCreateSerializer(
            data=request.data,
            context={'cart': cart}
        )
        serializer.is_valid(raise_exception=True)

        try:
            cart_item = CartService.add_to_cart(
                cart=cart,
                product=serializer.validated_data['product'],
                quantity=serializer.validated_data.get('quantity', 1)
            )

            return Response(
                CartItemSerializer(cart_item).data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=['Cart'])
class CartClearView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = CartService.get_or_create_cart(request.user)
        CartService.clear_cart(cart)

        return Response({
            'message': 'Cart cleared successfully'
        }, status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Cart'])
class CartValidateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = CartService.get_or_create_cart(request.user)
        validation_result = CartService.validate_cart_items(cart)

        return Response(validation_result)


@extend_schema(tags=['Cart'])
class CartSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = CartService.get_or_create_cart(request.user)
        summary = CartService.get_cart_summary(cart)

        return Response(summary)


@extend_schema(tags=['Cart'])
class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        cart = CartService.get_or_create_cart(request.user)
        return get_object_or_404(CartItem, pk=pk, cart=cart)

    def get(self, request, pk):
        cart_item = self.get_object(request, pk)
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    @extend_schema(request=CartItemUpdateSerializer)
    def patch(self, request, pk):
        cart_item = self.get_object(request, pk)

        serializer = CartItemUpdateSerializer(
            cart_item,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        try:
            updated_item = CartService.update_cart_item(
                cart_item,
                serializer.validated_data['quantity']
            )

            return Response(CartItemSerializer(updated_item).data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, pk):
        cart_item = self.get_object(request, pk)
        CartService.remove_from_cart(cart_item)

        return Response({
            'message': 'Item removed from cart'
        }, status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Cart'])
class CartItemIncreaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        cart = CartService.get_or_create_cart(request.user)
        cart_item = get_object_or_404(CartItem, pk=pk, cart=cart)

        try:
            updated_item = CartService.update_cart_item(
                cart_item,
                cart_item.quantity + 1
            )

            return Response(CartItemSerializer(updated_item).data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=['Cart'])
class CartItemDecreaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        cart = CartService.get_or_create_cart(request.user)
        cart_item = get_object_or_404(CartItem, pk=pk, cart=cart)

        if cart_item.quantity <= 1:
            return Response(
                {'error': 'Quantity cannot be less than 1. Remove item instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated_item = CartService.update_cart_item(
                cart_item,
                cart_item.quantity - 1
            )

            return Response(CartItemSerializer(updated_item).data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )