from django.urls import path
from .views.orders import order_detail
from .views.dashboard import view_dashboard

app_name = "tracking"

urlpatterns = [
    path("orders/", order_detail.detail, name="order_detail"),
    path("dashboard/", view_dashboard, name="dashboard"),
]
