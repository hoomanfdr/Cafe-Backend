from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cart.models import Cart
from products.models import Product
from .models import Order, OrderItem
from .serializers import OrderSerializer


class OrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).order_by("-created_at")


class OrderDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        )


class CreateOrderAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart = get_object_or_404(
            Cart,
            user=request.user,
        )

        if not cart.items.exists():
            return Response(
                {"detail": "Cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():

            cart_items = list(
                cart.items.select_related("product")
            )

            # Get product IDs
            product_ids = [
                item.product.id
                for item in cart_items
            ]

            # Lock products to prevent stock race conditions
            locked_products = {
                product.id: product
                for product in (
                    Product.objects
                    .select_for_update()
                    .filter(id__in=product_ids)
                )
            }

            # Check product availability after locking
            for item in cart_items:
                product = locked_products[item.product.id]

                if not product.is_available:
                    return Response(
                        {
                            "detail": (
                                f"Product '{product.name}' "
                                "is not available."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Check stock after locking products
            for item in cart_items:
                product = locked_products[item.product.id]

                if product.stock < item.quantity:
                    return Response(
                        {
                            "detail": (
                                f"Not enough stock for "
                                f"'{product.name}'. "
                                f"Available: {product.stock}, "
                                f"requested: {item.quantity}."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Create order
            order = Order.objects.create(
                user=request.user
            )

            # Create order items and decrease stock
            for item in cart_items:
                product = locked_products[item.product.id]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.price,
                )

                product.stock -= item.quantity

                product.save(
                    update_fields=["stock"]
                )

            # Clear cart after successful order
            cart.items.all().delete()

        serializer = OrderSerializer(order)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class CancelOrderAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        with transaction.atomic():

            # Lock the order while cancelling it
            order = get_object_or_404(
                Order.objects.select_for_update(),
                pk=pk,
                user=request.user,
            )

            # Only pending orders can be cancelled
            if order.status != "PENDING":
                return Response(
                    {
                        "detail": (
                            "Only pending orders can be cancelled."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Return stock to products
            order_items = order.items.select_related(
                "product"
            )

            for item in order_items:

                product = Product.objects.select_for_update().get(
                    id=item.product.id
                )

                product.stock += item.quantity

                product.save(
                    update_fields=["stock"]
                )

            # Change order status
            order.status = "CANCELLED"

            order.save(
                update_fields=["status"]
            )

        return Response(
            {
                "message": "Order cancelled successfully."
            },
            status=status.HTTP_200_OK,
        )