from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from products.models import Category, Product
from .models import Cart


class CartAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="testuser",
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

        self.client.force_authenticate(user=self.user)

    def test_get_cart(self):
        response = self.client.get("/api/cart/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"], self.user.id)
        self.assertEqual(response.data["items"], [])

    def test_add_product_to_cart(self):
        response = self.client.post(
            f"/api/cart/add/{self.product.id}/",
            {"quantity": 2},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["quantity"], 2)

        cart = Cart.objects.get(user=self.user)

        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(
            cart.items.first().quantity,
            2,
        )

    def test_add_same_product_increases_quantity(self):
        self.client.post(
            f"/api/cart/add/{self.product.id}/",
            {"quantity": 2},
            format="json",
        )

        response = self.client.post(
            f"/api/cart/add/{self.product.id}/",
            {"quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["quantity"], 5)

        cart = Cart.objects.get(user=self.user)

        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(
            cart.items.first().quantity,
            5,
        )

    def test_cannot_add_zero_quantity(self):
        response = self.client.post(
            f"/api/cart/add/{self.product.id}/",
            {"quantity": 0},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_cannot_add_negative_quantity(self):
        response = self.client.post(
            f"/api/cart/add/{self.product.id}/",
            {"quantity": -1},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_cannot_add_more_than_stock(self):
        response = self.client.post(
            f"/api/cart/add/{self.product.id}/",
            {"quantity": 11},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        cart = Cart.objects.filter(
            user=self.user
        ).first()

        if cart:
            self.assertEqual(cart.items.count(), 0)

    def test_cannot_add_unavailable_product(self):
        self.product.is_available = False
        self.product.save(
            update_fields=["is_available"]
        )

        response = self.client.post(
            f"/api/cart/add/{self.product.id}/",
            {"quantity": 1},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        cart = Cart.objects.filter(
            user=self.user
        ).first()

        if cart:
            self.assertEqual(cart.items.count(), 0)

    def test_remove_decreases_quantity(self):
        self.client.post(
            f"/api/cart/add/{self.product.id}/",
            {"quantity": 3},
            format="json",
        )

        response = self.client.delete(
            f"/api/cart/remove/{self.product.id}/"
        )

        self.assertEqual(response.status_code, 200)

        cart = Cart.objects.get(
            user=self.user
        )

        self.assertEqual(
            cart.items.first().quantity,
            2,
        )

    def test_remove_last_quantity_deletes_item(self):
        self.client.post(
            f"/api/cart/add/{self.product.id}/",
            {"quantity": 1},
            format="json",
        )

        response = self.client.delete(
            f"/api/cart/remove/{self.product.id}/"
        )

        self.assertEqual(response.status_code, 200)

        cart = Cart.objects.get(
            user=self.user
        )

        self.assertEqual(
            cart.items.count(),
            0,
        )

    def test_clear_cart(self):
        self.client.post(
            f"/api/cart/add/{self.product.id}/",
            {"quantity": 3},
            format="json",
        )

        response = self.client.delete(
            "/api/cart/clear/"
        )

        self.assertEqual(response.status_code, 200)

        cart = Cart.objects.get(
            user=self.user
        )

        self.assertEqual(
            cart.items.count(),
            0,
        )

    def test_cart_total(self):
        self.client.post(
            f"/api/cart/add/{self.product.id}/",
            {"quantity": 3},
            format="json",
        )

        response = self.client.get(
            "/api/cart/total/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["total_items"],
            1,
        )
        self.assertEqual(
            response.data["total_quantity"],
            3,
        )
        self.assertEqual(
            Decimal(str(response.data["total_price"])),
            Decimal("360000.00"),
        )