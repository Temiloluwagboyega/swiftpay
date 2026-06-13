from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from .models import PaymentLink


class CreateLinkSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=8, min_value=Decimal("0.00000001"))
    coin = serializers.ChoiceField(choices=PaymentLink.Coin.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)
    telegramUserId = serializers.CharField(required=False, allow_blank=True)
    telegramUsername = serializers.CharField(required=False, allow_blank=True, max_length=128)
    initData = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        from .telegram_auth import verify_telegram_init_data

        init_data = attrs.get("initData", "")
        user = verify_telegram_init_data(init_data)

        attrs["verified_user_id"] = str(user["id"])
        attrs["verified_username"] = user.get("username") or attrs.get("telegramUsername") or ""

        client_user_id = attrs.get("telegramUserId")
        if client_user_id and str(client_user_id) != attrs["verified_user_id"]:
            if not settings.DEBUG:
                raise serializers.ValidationError(
                    {"telegramUserId": "Does not match verified Telegram user."}
                )

        return attrs


class CreateLinkResponseSerializer(serializers.ModelSerializer):
    linkId = serializers.CharField(source="link_id")
    url = serializers.CharField(source="payment_url")
    expiresAt = serializers.DateTimeField(source="expires_at")

    class Meta:
        model = PaymentLink
        fields = ("linkId", "url", "expiresAt")


class LinkDetailSerializer(serializers.ModelSerializer):
    requesterUsername = serializers.CharField(source="requester_username")

    class Meta:
        model = PaymentLink
        fields = ("amount", "coin", "note", "requesterUsername", "status")


class PayLinkSerializer(serializers.Serializer):
    initData = serializers.CharField(required=False, allow_blank=True)
    payerUsername = serializers.CharField(required=False, allow_blank=True, max_length=128)


def count_links_created_today(user_id: str) -> int:
    start_of_day = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return PaymentLink.objects.filter(
        requester_user_id=str(user_id),
        created_at__gte=start_of_day,
    ).count()
