from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentLink
from .serializers import (
    CreateLinkResponseSerializer,
    CreateLinkSerializer,
    LinkDetailSerializer,
    PayLinkSerializer,
    count_links_created_today,
)
from .suggest_coin import get_coin_suggestion
from .telegram_auth import verify_telegram_init_data
from .telegram_notify import send_payment_notification


class CreateLinkView(APIView):
    def post(self, request):
        serializer = CreateLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_id = data["verified_user_id"]
        if count_links_created_today(user_id) >= settings.LINKS_PER_USER_PER_DAY:
            return Response(
                {"error": f"Rate limit exceeded. Max {settings.LINKS_PER_USER_PER_DAY} links per day."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        link = PaymentLink.create_link(
            amount=data["amount"],
            coin=data["coin"],
            note=data.get("note", ""),
            requester_user_id=user_id,
            requester_username=data["verified_username"],
        )

        return Response(
            CreateLinkResponseSerializer(link).data,
            status=status.HTTP_201_CREATED,
        )


class LinkDetailView(APIView):
    def get(self, request, link_id):
        link = get_object_or_404(PaymentLink, link_id=link_id)
        link.refresh_status()
        return Response(LinkDetailSerializer(link).data)


class PayLinkView(APIView):
    def post(self, request, link_id):
        link = get_object_or_404(PaymentLink, link_id=link_id)
        link.refresh_status()

        if link.status == PaymentLink.Status.EXPIRED:
            return Response(
                {"error": "This link has expired."},
                status=status.HTTP_410_GONE,
            )

        if link.status == PaymentLink.Status.PAID:
            return Response(
                {"error": "This link has already been paid."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = PayLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pay_data = serializer.validated_data

        payer_username = pay_data.get("payerUsername", "")
        init_data = pay_data.get("initData", "")
        if init_data:
            payer = verify_telegram_init_data(init_data)
            payer_username = payer.get("username") or payer_username

        from django.utils import timezone

        link.status = PaymentLink.Status.PAID
        link.paid_at = timezone.now()
        link.save(update_fields=["status", "paid_at"])

        send_payment_notification(
            chat_id=link.requester_user_id,
            amount=link.amount,
            coin=link.coin,
            note=link.note,
            payer_username=payer_username,
        )

        return Response({"success": True})


class SuggestCoinView(APIView):
    def get(self, request):
        return Response(get_coin_suggestion())


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok", "service": "swiftypay-api"})
