from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.OrderListCreateView.as_view(), name='order-list-create'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('<int:pk>/cancel/', views.OrderCancelView.as_view(), name='order-cancel'),
    path('statistics/', views.OrderStatisticsView.as_view(), name='order-statistics'),
    path('admin/', views.AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/<int:pk>/', views.AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('admin/<int:pk>/status/', views.AdminOrderStatusUpdateView.as_view(), name='admin-order-status'),
    path('admin/statistics/', views.AdminOrderStatisticsView.as_view(), name='admin-order-statistics'),
]