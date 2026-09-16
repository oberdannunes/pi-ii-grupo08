from rest_framework import generics

from tracking.filters import OrderFilter
from tracking.models.order import Order
from tracking.serializers import OrderSerializer


class OrderListAPIView(generics.ListAPIView):
    queryset = Order.objects.select_related('customer', 'carrier').order_by('-order_date')
    serializer_class = OrderSerializer
    filterset_class = OrderFilter