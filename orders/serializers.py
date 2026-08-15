from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "quantity",
            "price",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(
        many=True,
        read_only=True,
    )

    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "items",
            "total_price",
            "created_at",
        ]
        read_only_fields = [
            "user",
            "status",
            "items",
            "total_price",
            "created_at",
        ]

    def get_total_price(self, obj):
        return sum(
            item.price * item.quantity
            for item in obj.items.all()
        )