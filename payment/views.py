from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from orders.models import Order
from .models import Payment
from .serializers import PaymentSerializer


class CreatePaymentAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(
            Order,
            id=order_id,
            user=request.user,
        )

        if hasattr(order, "payment"):
            return Response(
                {"detail": "Payment already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        method = request.data.get("method")

        if not method:
            return Response(
                {"detail": "Payment method is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_amount = sum(
            item.price * item.quantity
            for item in order.items.all()
        )

        payment = Payment.objects.create(
            order=order,
            method=method,
            amount=total_amount,
            is_paid=True,
        )

        serializer = PaymentSerializer(payment)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )