from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient


class UserAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_register_user(self):
        response = self.client.post(
            "/api/register/",
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword123",
                "password2": "testpassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertTrue(
            User.objects.filter(
                username="testuser"
            ).exists()
        )

    def test_register_password_mismatch(self):
        response = self.client.post(
            "/api/register/",
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword123",
                "password2": "differentpassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            User.objects.filter(
                username="testuser"
            ).exists()
        )

    def test_register_password_too_short(self):
        response = self.client.post(
            "/api/register/",
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "123",
                "password2": "123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            User.objects.filter(
                username="testuser"
            ).exists()
        )

    def test_register_duplicate_username(self):
        User.objects.create_user(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.post(
            "/api/register/",
            {
                "username": "testuser",
                "email": "another@example.com",
                "password": "testpassword123",
                "password2": "testpassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_register_user_password_is_hashed(self):
        response = self.client.post(
            "/api/register/",
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword123",
                "password2": "testpassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        user = User.objects.get(
            username="testuser"
        )

        self.assertNotEqual(
            user.password,
            "testpassword123",
        )

        self.assertTrue(
            user.check_password(
                "testpassword123"
            )
        )

    def test_jwt_login(self):
        User.objects.create_user(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.post(
            "/api/token/",
            {
                "username": "testuser",
                "password": "testpassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "refresh",
            response.data,
        )

    def test_jwt_login_with_wrong_password(self):
        User.objects.create_user(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.post(
            "/api/token/",
            {
                "username": "testuser",
                "password": "wrongpassword",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_jwt_refresh_token(self):
        User.objects.create_user(
            username="testuser",
            password="testpassword123",
        )

        login_response = self.client.post(
            "/api/token/",
            {
                "username": "testuser",
                "password": "testpassword123",
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            200,
        )

        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            "/api/token/refresh/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "access",
            response.data,
        )

    def test_profile_requires_authentication(self):
        response = self.client.get(
            "/api/profile/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_authenticated_user_can_view_profile(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
        )

        self.client.force_authenticate(
            user=user
        )

        response = self.client.get(
            "/api/profile/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            user.id,
        )

        self.assertEqual(
            response.data["username"],
            "testuser",
        )

        self.assertEqual(
            response.data["email"],
            "test@example.com",
        )

    def test_profile_returns_only_authenticated_user(self):
        user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpassword123",
        )

        User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpassword123",
        )

        self.client.force_authenticate(
            user=user1
        )

        response = self.client.get(
            "/api/profile/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            user1.id,
        )

        self.assertEqual(
            response.data["username"],
            "user1",
        )

        self.assertNotEqual(
            response.data["username"],
            "user2",
        )

    def test_profile_returns_expected_fields(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="User",
        )

        self.client.force_authenticate(
            user=user
        )

        response = self.client.get(
            "/api/profile/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        expected_fields = {
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
        }

        self.assertEqual(
            set(response.data.keys()),
            expected_fields,
        )

    def test_invalid_refresh_token_is_rejected(self):
        response = self.client.post(
            "/api/token/refresh/",
            {
                "refresh": "invalid-refresh-token",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            401,
        )