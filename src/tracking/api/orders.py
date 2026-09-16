from rest_framework import generics

from tracking.filters import OrderFilter
from tracking.models.order import Order
from tracking.serializers import OrderSerializer

from rest_framework_api_key.permissions import HasAPIKey

class OrderListAPIView(generics.ListAPIView):
    permission_classes = [HasAPIKey]

    queryset = Order.objects.select_related('customer', 'carrier').order_by('-order_date')
    serializer_class = OrderSerializer
    filterset_class = OrderFilter