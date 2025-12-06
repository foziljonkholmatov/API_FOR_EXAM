from rest_framework import status, generics, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db.models import Sum, Avg
from datetime import timedelta
from django.utils import timezone

from apps.accounts.permissions import IsOwnerOrAdmin, IsAdminUser
from .models import Order
from .serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    OrderStatusUpdateSerializer,
    OrderCancelSerializer,
)
from .services import OrderService


@extend_schema(tags=['Orders'], summary='List/Create Orders', description='Get user orders or create new order')
class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderListSerializer

    def get_queryset(self):
        return OrderService.get_user_orders(self.request.user)

    @extend_schema(responses={201: OrderDetailSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = OrderService.create_order_from_cart(
                request.user,
                serializer.validated_data
            )

            return Response(
                OrderDetailSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=['Orders'])
class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)


@extend_schema(tags=['Orders'])
class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=OrderCancelSerializer, responses={200: OrderDetailSerializer})
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)

        serializer = OrderCancelSerializer(
            data=request.data,
            context={'order': order}
        )
        serializer.is_valid(raise_exception=True)

        try:
            cancelled_order = OrderService.cancel_order(
                order,
                serializer.validated_data.get('reason')
            )

            return Response(OrderDetailSerializer(cancelled_order).data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=['Orders'])
class OrderStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        statistics = OrderService.get_user_order_statistics(request.user)
        return Response(statistics)


@extend_schema(tags=['Admin - Orders'])
class AdminOrderListView(generics.ListAPIView):
    queryset = Order.objects.select_related('user').prefetch_related('items')
    serializer_class = OrderListSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'user']
    search_fields = ['user__username', 'user__email', 'phone']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']


@extend_schema(tags=['Admin - Orders'])
class AdminOrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAdminUser]


@extend_schema(tags=['Admin - Orders'])
class AdminOrderStatusUpdateView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=OrderStatusUpdateSerializer,
        responses={200: OrderDetailSerializer}
    )
    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_order = OrderService.update_order_status(
            order,
            serializer.validated_data['status']
        )

        return Response(OrderDetailSerializer(updated_order).data)


@extend_schema(tags=['Admin - Orders'])
class AdminOrderStatisticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):

        orders = Order.objects.all()

        stats = {
            'total_orders': orders.count(),
            'total_revenue': orders.exclude(
                status=Order.OrderStatus.CANCELLED
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,

            'status_breakdown': {
                status: orders.filter(status=status).count()
                for status, _ in Order.OrderStatus.choices
            },

            'average_order_value': orders.exclude(
                status=Order.OrderStatus.CANCELLED
            ).aggregate(Avg('total_amount'))['total_amount__avg'] or 0,
        }

        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_orders = orders.filter(created_at__gte=thirty_days_ago)

        stats['last_30_days'] = {
            'orders_count': recent_orders.count(),
            'revenue': recent_orders.exclude(
                status=Order.OrderStatus.CANCELLED
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        }

        return Response(stats)