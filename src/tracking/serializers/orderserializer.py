from rest_framework import serializers

from ..models.order import Order


class OrderSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_cnpj = serializers.CharField(source='customer.cnpj', read_only=True)
    carrier_name = serializers.CharField(source='carrier.name', read_only=True)

    class Meta:
        model = Order
        fields = [
#            'id',
            'nfe',
            'status',
            'status_display',
            'order_date',
            'collection_date',
            'delivery_date',
            'customer_name',
            'customer_cnpj',
            'carrier_name',
        ]
