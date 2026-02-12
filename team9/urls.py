from django.urls import path
from . import views

urlpatterns = [
    path("", views.base),
    path("ping/", views.ping),
    path("map/", views.map_view),
    path("api/mock-facilities/", views.mock_facilities_api),
]
