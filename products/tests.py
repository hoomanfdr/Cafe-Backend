from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Category, Product


class ProductAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.category_espresso = Category.objects.create(
            name="Espresso",
            description="Espresso products",
        )

        self.category_cold = Category.objects.create(
            name="Cold Drinks",
            description="Cold drinks",
        )

        self.product_espresso = Product.objects.create(
            category=self.category_espresso,
            name="Espresso",
            description="Classic espresso coffee",
            price=Decimal("120000.00"),
            stock=10,
            is_available=True,
        )

        self.product_latte = Product.objects.create(
            category=self.category_espresso,
            name="Latte",
            description="Milk coffee",
            price=Decimal("150000.00"),
            stock=5,
            is_available=True,
        )

        self.product_ice = Product.objects.create(
            category=self.category_cold,
            name="Iced Coffee",
            description="Cold coffee drink",
            price=Decimal("180000.00"),
            stock=8,
            is_available=True,
        )

        self.product_unavailable = Product.objects.create(
            category=self.category_cold,
            name="Unavailable Coffee",
            description="Currently unavailable",
            price=Decimal("100000.00"),
            stock=0,
            is_available=False,
        )

    def test_product_list(self):
        response = self.client.get(
            "/api/products/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            4,
        )

    def test_product_detail(self):
        response = self.client.get(
            f"/api/products/{self.product_espresso.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            self.product_espresso.id,
        )

        self.assertEqual(
            response.data["name"],
            "Espresso",
        )

        self.assertEqual(
            response.data["price"],
            "120000.00",
        )

    def test_product_detail_not_found(self):
        response = self.client.get(
            "/api/products/9999/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_category_list(self):
        response = self.client.get(
            "/api/categories/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            2,
        )

    def test_search_products_by_name(self):
        response = self.client.get(
            "/api/products/?search=Espresso"
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
            response.data["results"][0]["name"],
            "Espresso",
        )

    def test_search_products_by_description(self):
        response = self.client.get(
            "/api/products/?search=Milk"
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
            response.data["results"][0]["name"],
            "Latte",
        )

    def test_filter_products_by_category(self):
        response = self.client.get(
            f"/api/products/?category={self.category_espresso.id}"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            2,
        )

        product_names = {
            product["name"]
            for product in response.data["results"]
        }

        self.assertEqual(
            product_names,
            {"Espresso", "Latte"},
        )

    def test_filter_products_by_availability(self):
        response = self.client.get(
            "/api/products/?is_available=true"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            3,
        )

        for product in response.data["results"]:
            self.assertTrue(
                product["is_available"]
            )

    def test_filter_unavailable_products(self):
        response = self.client.get(
            "/api/products/?is_available=false"
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
            response.data["results"][0]["name"],
            "Unavailable Coffee",
        )

    def test_order_products_by_price_ascending(self):
        response = self.client.get(
            "/api/products/?ordering=price"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        prices = [
            Decimal(product["price"])
            for product in response.data["results"]
        ]

        self.assertEqual(
            prices,
            sorted(prices),
        )

    def test_order_products_by_price_descending(self):
        response = self.client.get(
            "/api/products/?ordering=-price"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        prices = [
            Decimal(product["price"])
            for product in response.data["results"]
        ]

        self.assertEqual(
            prices,
            sorted(prices, reverse=True),
        )

    def test_order_products_by_name(self):
        response = self.client.get(
            "/api/products/?ordering=name"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        names = [
            product["name"]
            for product in response.data["results"]
        ]

        self.assertEqual(
            names,
            sorted(names),
        )

    def test_pagination(self):
        response = self.client.get(
            "/api/products/?page=1"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "count",
            response.data,
        )

        self.assertIn(
            "next",
            response.data,
        )

        self.assertIn(
            "previous",
            response.data,
        )

        self.assertIn(
            "results",
            response.data,
        )

    def test_product_contains_category_data(self):
        response = self.client.get(
            f"/api/products/{self.product_espresso.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["category"]["id"],
            self.category_espresso.id,
        )

        self.assertEqual(
            response.data["category"]["name"],
            "Espresso",
        )

    def test_product_list_default_ordering(self):
        response = self.client.get(
            "/api/products/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        names = [
            product["name"]
            for product in response.data["results"]
        ]

        self.assertEqual(
            names,
            sorted(names),
        )