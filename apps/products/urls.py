from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'products'

router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='category')
router.register('products', views.ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]