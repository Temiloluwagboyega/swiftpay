from django.urls import path

from .views import CreateLinkView, HealthView, LinkDetailView, PayLinkView, SuggestCoinView

urlpatterns = [
    path("links/create", CreateLinkView.as_view(), name="link-create"),
    path("links/<str:link_id>", LinkDetailView.as_view(), name="link-detail"),
    path("links/<str:link_id>/pay", PayLinkView.as_view(), name="link-pay"),
    path("suggest-coin", SuggestCoinView.as_view(), name="suggest-coin"),
]

health_urlpatterns = [
    path("", HealthView.as_view(), name="health"),
]
