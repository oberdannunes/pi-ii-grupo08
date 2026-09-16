from django.urls import include, path
from tracking.api.orders import OrderListAPIView

urlpatterns = [
    path("tracking/", include("tracking.api.urls")),
]
