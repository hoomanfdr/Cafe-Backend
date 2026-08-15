from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "method",
            "amount",
            "is_paid",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "order",
            "amount",
            "is_paid",
            "created_at",
        ]