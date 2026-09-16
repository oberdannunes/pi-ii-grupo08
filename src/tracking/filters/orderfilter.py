import django_filters

from ..models.order import Order

class OrderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Order.STATUS_CHOICES)
    nfe = django_filters.CharFilter(lookup_expr='exact')
    customer_cnpj = django_filters.CharFilter(field_name='customer__cnpj', lookup_expr='exact')
    order_date_after = django_filters.DateFilter(field_name='order_date', lookup_expr='gte')
    order_date_before = django_filters.DateFilter(field_name='order_date', lookup_expr='lte')

    class Meta:
        model = Order
        fields = [
            'status',
            'nfe',
            'customer_cnpj',
            'order_date_after',
            'order_date_before',
        ]
