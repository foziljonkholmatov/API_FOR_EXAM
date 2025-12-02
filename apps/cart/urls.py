from django.urls import path

from . import views

app_name = 'cart'

urlpatterns = [
    # Cart operations
    path('', views.CartView.as_view(), name='cart'),
    path('clear/', views.CartClearView.as_view(), name='cart-clear'),
    path('validate/', views.CartValidateView.as_view(), name='cart-validate'),
    path('summary/', views.CartSummaryView.as_view(), name='cart-summary'),

    # Cart item operations
    path('items/<int:pk>/', views.CartItemDetailView.as_view(), name='cart-item-detail'),
    path('items/<int:pk>/increase/', views.CartItemIncreaseView.as_view(), name='cart-item-increase'),
    path('items/<int:pk>/decrease/', views.CartItemDecreaseView.as_view(), name='cart-item-decrease'),
]