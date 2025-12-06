from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from django.db.models import Q, Count

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
    list=extend_schema(
        tags=['Categories'],
        summary='List All Categories',
        description='Get list of all product categories'
    ),
    retrieve=extend_schema(
        tags=['Categories'],
        summary='Get Category Details',
        description='Get specific category by ID'
    ),
    create=extend_schema(
        tags=['Admin - Categories'],
        summary='Create Category',
        description='Create new category (Admin only)'
    ),
    update=extend_schema(
        tags=['Admin - Categories'],
        summary='Update Category',
        description='Update category (Admin only)'
    ),
    partial_update=extend_schema(
        tags=['Admin - Categories'],
        summary='Partial Update Category',
        description='Partial update category (Admin only)'
    ),
    destroy=extend_schema(
        tags=['Admin - Categories'],
        summary='Delete Category',
        description='Delete category (Admin only)'
    ),
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

    @extend_schema(
        tags=['Categories'],
        summary='Get Category Products',
        description='Get all products in a specific category'
    )
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        category = self.get_object()
        products = category.products.filter(is_active=True)

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=['Products'],
        summary='List All Products',
        description='Get list of all products with filtering and search options',
        examples=[
            OpenApiExample(
                'Products List Response',
                value={
                    'count': 50,
                    'next': 'http://localhost:8000/api/products/?page=2',
                    'previous': None,
                    'results': [
                        {
                            'id': 1,
                            'name': 'iPhone 15 Pro',
                            'slug': 'iphone-15-pro',
                            'price': '12999999.00',
                            'final_price': '11999999.00',
                            'stock': 50,
                            'is_in_stock': True,
                            'category_name': 'Smartphones'
                        }
                    ]
                },
                response_only=True
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['Products'],
        summary='Get Product Details',
        description='Get detailed information about a specific product',
        examples=[
            OpenApiExample(
                'Product Detail Response',
                value={
                    'id': 1,
                    'name': 'iPhone 15 Pro',
                    'slug': 'iphone-15-pro',
                    'description': 'Latest iPhone with A17 Pro chip',
                    'price': '12999999.00',
                    'discount_price': '11999999.00',
                    'final_price': '11999999.00',
                    'stock': 50,
                    'category_name': 'Smartphones',
                    'is_in_stock': True,
                    'is_on_sale': True
                },
                response_only=True
            )
        ]
    ),
    create=extend_schema(
        tags=['Admin - Products'],
        summary='Create Product',
        description='Create new product (Admin only)',
        examples=[
            OpenApiExample(
                'Create Product Request',
                value={
                    'name': 'iPhone 15 Pro Max',
                    'description': 'Latest Apple flagship',
                    'price': '14999999.00',
                    'stock': 30,
                    'category': 1,
                    'is_active': True
                },
                request_only=True
            )
        ]
    ),
    update=extend_schema(
        tags=['Admin - Products'],
        summary='Update Product',
        description='Update product (Admin only)'
    ),
    partial_update=extend_schema(
        tags=['Admin - Products'],
        summary='Partial Update Product',
        description='Partial update product (Admin only)'
    ),
    destroy=extend_schema(
        tags=['Admin - Products'],
        summary='Delete Product',
        description='Delete product (Admin only)'
    ),
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

        # Show only active products for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)

        return queryset

    @extend_schema(
        tags=['Products'],
        summary='Featured Products',
        description='Get list of featured products',
        responses={200: ProductListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        products = self.get_queryset().filter(is_featured=True, is_active=True)[:10]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Products'],
        summary='On Sale Products',
        description='Get products currently on sale',
        responses={200: ProductListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def on_sale(self, request):
        from django.db.models import F

        products = self.get_queryset().filter(
            is_active=True,
            discount_price__isnull=False,
            discount_price__lt=F('price')
        )[:20]

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Admin - Products'],
        summary='Update Stock',
        description='Update product stock quantity (Admin only)',
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
        tags=['Admin - Products'],
        summary='Upload Images',
        description='Upload additional product images (Admin only)',
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
        summary='Search Products',
        description='Advanced product search',
        responses={200: ProductListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')

        if not query:
            return Response([], status=status.HTTP_200_OK)

        products = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()[:20]

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)