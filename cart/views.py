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
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


class AddToCartAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        cart, created = Cart.objects.get_or_create(user=request.user)

        product = get_object_or_404(Product, id=product_id)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        return Response(
            {"message": "Product added to cart"},
            status=status.HTTP_200_OK,
        )


class RemoveFromCartAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        cart = get_object_or_404(Cart, user=request.user)

        cart_item = get_object_or_404(
            CartItem,
            cart=cart,
            product_id=product_id,
        )

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()

            return Response(
                {"message": "Product quantity decreased"},
                status=status.HTTP_200_OK,
            )

        cart_item.delete()

        return Response(
            {"message": "Product removed from cart"},
            status=status.HTTP_200_OK,
        )


class ClearCartAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = get_object_or_404(Cart, user=request.user)

        cart.items.all().delete()

        return Response(
            {"message": "Cart cleared successfully"},
            status=status.HTTP_200_OK,
        )


class CartTotalAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)

        total_items = cart.items.count()

        total_quantity = sum(
            item.quantity for item in cart.items.all()
        )

        total_price = sum(
            item.quantity * item.product.price
            for item in cart.items.all()
        )

        return Response(
            {
                "total_items": total_items,
                "total_quantity": total_quantity,
                "total_price": total_price,
            },
            status=status.HTTP_200_OK,
        )