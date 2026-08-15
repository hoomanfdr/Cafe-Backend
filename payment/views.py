from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Order
from .models import Payment
from .serializers import PaymentSerializer


class CreatePaymentAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):

        with transaction.atomic():

            order = get_object_or_404(
                Order.objects.select_for_update(),
                id=order_id,
                user=request.user,
            )

            # Only pending orders can be paid
            if order.status != "PENDING":
                return Response(
                    {
                        "detail": (
                            "Only pending orders can be paid."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Prevent duplicate payment
            if hasattr(order, "payment"):
                return Response(
                    {
                        "detail": "Payment already exists."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Calculate total amount from Order
            total_amount = sum(
                item.price * item.quantity
                for item in order.items.all()
            )

            payment = Payment.objects.create(
                order=order,
                method="CASH",
                amount=total_amount,
                is_paid=True,
            )

            # Mark order as paid
            order.status = "PAID"
            order.save(
                update_fields=["status"]
            )

        serializer = PaymentSerializer(payment)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )