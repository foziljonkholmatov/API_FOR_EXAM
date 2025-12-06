

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import Q, Count, F

from apps.accounts.permissions import IsAdminOrReadOnly
from .models import Category, Product
from .serializers import (
    CategorySerializer,
    CategoryListSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    ProductStockUpdateSerializer,
    ProductImageSerializer,
)
from .filters import ProductFilter, CategoryFilter


@extend_schema_view(
    list=extend_schema(tags=['Categories']),
    retrieve=extend_schema(tags=['Categories']),
    create=extend_schema(tags=['Admin - Categories']),
    update=extend_schema(tags=['Admin - Categories']),
    partial_update=extend_schema(tags=['Admin - Categories']),
    destroy=extend_schema(tags=['Admin - Categories']),
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.annotate(
        products_count=Count('products', filter=Q(products__is_active=True))
    )
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CategoryFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'products_count']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    @extend_schema(tags=['Categories'])
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        category = self.get_object()
        products = category.products.filter(is_active=True)
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Products']),
    retrieve=extend_schema(tags=['Products']),
    create=extend_schema(tags=['Admin - Products']),
    update=extend_schema(tags=['Admin - Products']),
    partial_update=extend_schema(tags=['Admin - Products']),
    destroy=extend_schema(tags=['Admin - Products']),
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').prefetch_related('images')
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['name', 'price', 'stock', 'created_at']
    ordering = ['-created_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        elif self.action == 'update_stock':
            return ProductStockUpdateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    @extend_schema(
        tags=['Products'],
        responses={200: ProductListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def featured(self, request):
        products = self.get_queryset().filter(is_featured=True, is_active=True)[:10]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Products'],
        responses={200: ProductListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def on_sale(self, request):
        products = self.get_queryset().filter(
            is_active=True,
            discount_price__isnull=False,
            discount_price__lt=F('price')
        )[:20]

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Admin - Products'],
        request=ProductStockUpdateSerializer,
        responses={200: ProductDetailSerializer}
    )
    @action(detail=True, methods=['patch'], permission_classes=[IsAdminOrReadOnly])
    def update_stock(self, request, slug=None):
        product = self.get_object()
        serializer = ProductStockUpdateSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(ProductDetailSerializer(product).data)

    @extend_schema(
        tags=['Admin -Products'],
        request=ProductImageSerializer(many=True),
        responses={201: ProductImageSerializer(many=True)}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrReadOnly])
    def upload_images(self, request, slug=None):
        product = self.get_object()
        images_data = request.data.get('images', [])

        created_images = []
        for image_data in images_data:
            image_data['product'] = product.id
            serializer = ProductImageSerializer(data=image_data)
            if serializer.is_valid():
                serializer.save(product=product)
                created_images.append(serializer.data)
        return Response(created_images, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['Products'],
        responses={200: ProductListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')

        if not query:
            return Response([], status=status.HTTP_200_OK)
        products = self.get_queryset().filter(
            Q(name__icontains=query),
            Q(description__icotains=query),
            Q(short_description__icontains=query),
            Q(category_name__icontians=query)
        ).distinct()[:20]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)
