import secrets
import string

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_link_id(length: int = 5) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class PaymentLink(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        EXPIRED = "expired", "Expired"

    class Coin(models.TextChoices):
        USDT = "USDT", "USDT"
        BTC = "BTC", "BTC"
        ETH = "ETH", "ETH"

    link_id = models.CharField(max_length=16, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    coin = models.CharField(max_length=8, choices=Coin.choices)
    note = models.TextField(blank=True, default="")
    requester_user_id = models.CharField(max_length=32, db_index=True)
    requester_username = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["requester_user_id", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.link_id} ({self.status})"

    @classmethod
    def create_link(
        cls,
        *,
        amount,
        coin,
        note,
        requester_user_id,
        requester_username,
    ) -> "PaymentLink":
        expires_at = timezone.now() + timezone.timedelta(hours=settings.LINK_EXPIRY_HOURS)
        for _ in range(10):
            link_id = generate_link_id()
            if not cls.objects.filter(link_id=link_id).exists():
                return cls.objects.create(
                    link_id=link_id,
                    amount=amount,
                    coin=coin,
                    note=note or "",
                    requester_user_id=str(requester_user_id),
                    requester_username=requester_username or "",
                    expires_at=expires_at,
                )
        raise RuntimeError("Could not generate unique link id")

    def refresh_status(self) -> None:
        if self.status == self.Status.PENDING and timezone.now() >= self.expires_at:
            self.status = self.Status.EXPIRED
            self.save(update_fields=["status"])

    @property
    def payment_url(self) -> str:
        return f"{settings.FRONTEND_BASE_URL}/pay/{self.link_id}"
