from django.db import models

from orders.models import Order


class Payment(models.Model):

    PAYMENT_METHODS = [
        ("CASH", "Cash"),
    ]

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="payment",
    )

    method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default="CASH",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    is_paid = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Payment #{self.id}"