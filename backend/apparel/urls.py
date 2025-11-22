from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApparelProductViewSet
from .order_views import create_whatsapp_order
from .payment_views import create_razorpay_order, verify_payment

# Create router and register viewsets
router = DefaultRouter()
router.register(r'apparel', ApparelProductViewSet, basename='apparel')

urlpatterns = [
    path('', include(router.urls)),
    path('orders/whatsapp/', create_whatsapp_order, name='whatsapp-order'),
    path('payments/create-order/', create_razorpay_order, name='create-razorpay-order'),
    path('payments/verify/', verify_payment, name='verify-payment'),
]
