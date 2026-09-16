from django.urls import path
from .orders import OrderListAPIView

urlpatterns = [
    path("orders/", OrderListAPIView.as_view(), name="api_order_list"),
]
