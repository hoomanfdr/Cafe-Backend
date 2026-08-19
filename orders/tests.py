from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from cart.models import Cart, CartItem
from products.models import Category, Product

from .models import Order


class OrderAPITestCase(TestCase):

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

    def add_product_to_cart(self, quantity=1):
        cart = Cart.objects.create(
            user=self.user
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=quantity,
        )

        return cart

    def test_cannot_create_order_with_empty_cart(self):
        Cart.objects.create(
            user=self.user
        )

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["detail"],
            "Cart is empty.",
        )

    def test_create_order(self):
        self.add_product_to_cart(quantity=2)

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        order = Order.objects.get(
            user=self.user
        )

        self.assertEqual(
            order.status,
            "PENDING",
        )

        self.assertEqual(
            order.items.count(),
            1,
        )

        order_item = order.items.first()

        self.assertEqual(
            order_item.product,
            self.product,
        )

        self.assertEqual(
            order_item.quantity,
            2,
        )

        self.assertEqual(
            order_item.price,
            Decimal("120000.00"),
        )

    def test_order_decreases_product_stock(self):
        self.add_product_to_cart(quantity=3)

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            7,
        )

    def test_order_clears_cart(self):
        cart = self.add_product_to_cart(quantity=2)

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        cart.refresh_from_db()

        self.assertEqual(
            cart.items.count(),
            0,
        )

    def test_order_stores_price_snapshot(self):
        self.add_product_to_cart(quantity=2)

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        order = Order.objects.get(
            user=self.user
        )

        order_item = order.items.first()

        self.assertEqual(
            order_item.price,
            Decimal("120000.00"),
        )

        self.product.price = Decimal("150000.00")
        self.product.save(
            update_fields=["price"]
        )

        order_item.refresh_from_db()

        self.assertEqual(
            order_item.price,
            Decimal("120000.00"),
        )

    def test_cannot_create_order_when_stock_is_not_enough(self):
        self.add_product_to_cart(quantity=11)

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            10,
        )

        self.assertEqual(
            Order.objects.filter(
                user=self.user
            ).count(),
            0,
        )

    def test_cannot_create_order_for_unavailable_product(self):
        self.product.is_available = False
        self.product.save(
            update_fields=["is_available"]
        )

        self.add_product_to_cart(quantity=1)

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            Order.objects.filter(
                user=self.user
            ).count(),
            0,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            10,
        )

    def test_list_orders_returns_only_current_users_orders(self):
        Order.objects.create(
            user=self.user
        )

        Order.objects.create(
            user=self.other_user
        )

        response = self.client.get(
            "/api/orders/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["user"],
            self.user.id,
        )

    def test_user_cannot_access_another_users_order(self):
        order = Order.objects.create(
            user=self.other_user
        )

        response = self.client.get(
            f"/api/orders/{order.id}/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_user_can_access_own_order(self):
        order = Order.objects.create(
            user=self.user
        )

        response = self.client.get(
            f"/api/orders/{order.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            order.id,
        )

    def test_pending_order_can_be_cancelled(self):
        self.add_product_to_cart(quantity=3)

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        order = Order.objects.get(
            user=self.user
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            7,
        )

        response = self.client.post(
            f"/api/orders/{order.id}/cancel/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            "CANCELLED",
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            10,
        )

    def test_paid_order_cannot_be_cancelled(self):
        self.add_product_to_cart(quantity=2)

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        order = Order.objects.get(
            user=self.user
        )

        order.status = "PAID"
        order.save(
            update_fields=["status"]
        )

        self.product.refresh_from_db()

        stock_before_cancel = self.product.stock

        response = self.client.post(
            f"/api/orders/{order.id}/cancel/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            "PAID",
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            stock_before_cancel,
        )

    def test_cancelled_order_does_not_restore_stock_twice(self):
        self.add_product_to_cart(quantity=2)

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        order = Order.objects.get(
            user=self.user
        )

        response = self.client.post(
            f"/api/orders/{order.id}/cancel/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            10,
        )

        response = self.client.post(
            f"/api/orders/{order.id}/cancel/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            10,
        )

    def test_order_total_price(self):
        self.add_product_to_cart(quantity=3)

        response = self.client.post(
            "/api/orders/create/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        order = Order.objects.get(
            user=self.user
        )

        response = self.client.get(
            f"/api/orders/{order.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            Decimal(str(response.data["total_price"])),
            Decimal("360000.00"),
        )