from django.contrib import admin

from .models import PaymentLink


@admin.register(PaymentLink)
class PaymentLinkAdmin(admin.ModelAdmin):
    list_display = (
        "link_id",
        "amount",
        "coin",
        "requester_username",
        "status",
        "created_at",
        "expires_at",
    )
    list_filter = ("status", "coin")
    search_fields = ("link_id", "requester_username", "requester_user_id")
    readonly_fields = ("created_at", "paid_at")
