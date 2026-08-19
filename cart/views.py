from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from products.models import Product
from .models import Cart, CartItem
from .serializers import CartSerializer


class CartAPIView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(
            user=self.request.user
        )
        return cart


class AddToCartAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):

        product = get_object_or_404(
            Product,
            id=product_id
        )

        # Check product availability
        if not product.is_available:
            return Response(
                {
                    "detail": (
                        f"Product '{product.name}' is not available."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        quantity = request.data.get("quantity", 1)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response(
                {
                    "detail": "Quantity must be a valid integer."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity <= 0:
            return Response(
                {
                    "detail": "Quantity must be greater than 0."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():

            cart, created = Cart.objects.get_or_create(
                user=request.user
            )

            cart_item = CartItem.objects.filter(
                cart=cart,
                product=product,
            ).first()

            if cart_item:
                new_quantity = cart_item.quantity + quantity
            else:
                new_quantity = quantity

            # Check stock BEFORE creating/updating CartItem
            if new_quantity > product.stock:
                return Response(
                    {
                        "detail": (
                            f"Not enough stock for '{product.name}'. "
                            f"Available: {product.stock}, "
                            f"requested: {new_quantity}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if cart_item:
                cart_item.quantity = new_quantity
                cart_item.save(update_fields=["quantity"])
            else:
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=quantity,
                )

        return Response(
            {
                "message": "Product added to cart",
                "quantity": new_quantity,
            },
            status=status.HTTP_200_OK,
        )


class RemoveFromCartAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):

        cart = get_object_or_404(
            Cart,
            user=request.user
        )

        cart_item = get_object_or_404(
            CartItem,
            cart=cart,
            product_id=product_id,
        )

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save(update_fields=["quantity"])

            return Response(
                {
                    "message": "Product quantity decreased"
                },
                status=status.HTTP_200_OK,
            )

        cart_item.delete()

        return Response(
            {
                "message": "Product removed from cart"
            },
            status=status.HTTP_200_OK,
        )


class ClearCartAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):

        cart = get_object_or_404(
            Cart,
            user=request.user
        )

        cart.items.all().delete()

        return Response(
            {
                "message": "Cart cleared successfully"
            },
            status=status.HTTP_200_OK,
        )


class CartTotalAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        items = cart.items.select_related("product").all()

        total_items = len(items)

        total_quantity = sum(
            item.quantity
            for item in items
        )

        total_price = sum(
            item.quantity * item.product.price
            for item in items
        )

        return Response(
            {
                "total_items": total_items,
                "total_quantity": total_quantity,
                "total_price": total_price,
            },
            status=status.HTTP_200_OK,
        )