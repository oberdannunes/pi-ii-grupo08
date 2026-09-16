from django.urls import include, path
from .views import home

app_name = "core"

urlpatterns = [
    path("", home.index, name="home"),
    path("api/", include("core.api.urls")),
]