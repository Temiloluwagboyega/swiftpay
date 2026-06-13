from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("links.urls")),
    path("health/", include("links.health_urls")),
]
