from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cart.models import Cart
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
        cart = Cart.objects.get(user=request.user)

        if not cart.items.exists():
            return Response(
                {"detail": "Cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = Order.objects.create(user=request.user)

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )

        cart.items.all().delete()

        serializer = OrderSerializer(order)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CancelOrderAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = generics.get_object_or_404(
            Order,
            pk=pk,
            user=request.user,
        )

        if order.status != "PENDING":
            return Response(
                {"detail": "Only pending orders can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = "CANCELLED"
        order.save()

        return Response(
            {"message": "Order cancelled successfully."},
            status=status.HTTP_200_OK,
        )