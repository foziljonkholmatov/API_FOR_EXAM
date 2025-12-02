from django_filters import rest_framework as filters
from django.db import models
from django.db.models import Q

from .models import Category, Product


class ProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')

    category = filters.ModelChoiceFilter(queryset=Category.objects.filter(is_active=True))
    category_slug = filters.CharFilter(field_name='category_slug', lookup_expr='exact')

    in_stock = filters.BooleanFilter(method='filter_in_stock')

    is_featured = filters.BooleanFilter()
    is_active = filters.BooleanFilter()

    on_sale = filters.BooleanFilter(method='filter_on_sale')

    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Product
        fields = [
            'category', 'category_slug', 'is_active',
            'is_featured', 'in_stock', 'on_sale'
        ]

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)

    def filter_on_sale(self, queryset, name, value):
        if value:
            return queryset.filter(
                discount_price__isnull=False,
                discount_price__lt=models.F('price')
            )
        return queryset

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value),
            Q(description__icontains=value),
            Q(short_description__icontains=value),
            Q(category_name__icontains=value)
        )


class CategoryFilter(filters.FilterSet):
    search = filters.CharFilter(method='filter_search')
    is_active = filters.BooleanFilter()

    class Meta:
        model = Category
        fields = ['is_active']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value),
            Q(description__icontains=value)
        )
