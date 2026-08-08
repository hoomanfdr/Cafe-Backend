from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "method",
        "amount",
        "is_paid",
        "created_at",
    )

    list_filter = (
        "method",
        "is_paid",
    )

    search_fields = (
        "order__id",
    )