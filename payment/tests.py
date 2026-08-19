from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from cart.models import Cart, CartItem
from orders.models import Order
from products.models import Category, Product

from .models import Payment


class PaymentAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            password="testpassword123",
        )

        self.category = Category.objects.create(
            name="Test Category",
            description="Test category",
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Test Espresso",
            description="Test product",
            price=Decimal("120000.00"),
            stock=10,
            is_available=True,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def create_pending_order(self, quantity=1):
        cart = Cart.objects.create(
            user=self.user
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=quantity,
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        return Order.objects.get(
            user=self.user
        )

    def test_create_payment(self):
        order = self.create_pending_order(
            quantity=2
        )

        response = self.client.post(
            f"/api/payment/{order.id}/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["order"],
            order.id,
        )

        self.assertEqual(
            response.data["method"],
            "CASH",
        )

        self.assertEqual(
            Decimal(str(response.data["amount"])),
            Decimal("240000.00"),
        )

        self.assertTrue(
            response.data["is_paid"]
        )

    def test_payment_marks_order_as_paid(self):
        order = self.create_pending_order()

        self.assertEqual(
            order.status,
            "PENDING",
        )

        response = self.client.post(
            f"/api/payment/{order.id}/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            "PAID",
        )

    def test_payment_amount_is_calculated_from_order(self):
        order = self.create_pending_order(
            quantity=3
        )

        response = self.client.post(
            f"/api/payment/{order.id}/",
            {
                "amount": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        payment = Payment.objects.get(
            order=order
        )

        self.assertEqual(
            payment.amount,
            Decimal("360000.00"),
        )

    def test_duplicate_payment_is_rejected(self):
        order = self.create_pending_order()

        first_response = self.client.post(
            f"/api/payment/{order.id}/",
            {},
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            201,
        )

        second_response = self.client.post(
            f"/api/payment/{order.id}/",
            {},
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            400,
        )

        self.assertEqual(
            second_response.data["detail"],
            "Only pending orders can be paid.",
        )

        self.assertEqual(
            Payment.objects.filter(
                order=order
            ).count(),
            1,
        )

    def test_cancelled_order_cannot_be_paid(self):
        order = self.create_pending_order()

        order.status = "CANCELLED"
        order.save(
            update_fields=["status"]
        )

        response = self.client.post(
            f"/api/payment/{order.id}/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["detail"],
            "Only pending orders can be paid.",
        )

        self.assertFalse(
            Payment.objects.filter(
                order=order
            ).exists()
        )

    def test_paid_order_cannot_be_paid_again(self):
        order = self.create_pending_order()

        response = self.client.post(
            f"/api/payment/{order.id}/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        response = self.client.post(
            f"/api/payment/{order.id}/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["detail"],
            "Only pending orders can be paid.",
        )

        self.assertEqual(
            Payment.objects.filter(
                order=order
            ).count(),
            1,
        )

    def test_user_cannot_pay_another_users_order(self):
        other_order = Order.objects.create(
            user=self.other_user
        )

        response = self.client.post(
            f"/api/payment/{other_order.id}/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertFalse(
            Payment.objects.filter(
                order=other_order
            ).exists()
        )

    def test_payment_uses_cash_method(self):
        order = self.create_pending_order()

        response = self.client.post(
            f"/api/payment/{order.id}/",
            {
                "method": "CARD",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        payment = Payment.objects.get(
            order=order
        )

        self.assertEqual(
            payment.method,
            "CASH",
        )

    def test_payment_is_marked_as_paid(self):
        order = self.create_pending_order()

        response = self.client.post(
            f"/api/payment/{order.id}/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        payment = Payment.objects.get(
            order=order
        )

        self.assertTrue(
            payment.is_paid
        )

    def test_payment_amount_matches_order_total(self):
        order = self.create_pending_order(
            quantity=2
        )

        order_item = order.items.first()

        expected_total = (
            order_item.price * order_item.quantity
        )

        response = self.client.post(
            f"/api/payment/{order.id}/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        payment = Payment.objects.get(
            order=order
        )

        self.assertEqual(
            payment.amount,
            expected_total,
        )