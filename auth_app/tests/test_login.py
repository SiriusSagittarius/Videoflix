from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.tests.helpers import EMAIL, PASSWORD, create_user, login
from auth_app.utils import ACCOUNT_NOT_ACTIVE_MESSAGE, INVALID_INPUT_MESSAGE

LOGIN_URL = "/api/login/"
INVALID_INPUT = {"detail": INVALID_INPUT_MESSAGE}
COOKIE_LIFETIMES = {"access_token": 30 * 60, "refresh_token": 24 * 60 * 60}


class LoginTests(APITestCase):
    """POST /api/login/"""

    def setUp(self):
        """Create an active user."""
        self.user = create_user()

    def test_answers_with_user_data(self):
        """A valid login answers like the endpoint documentation."""
        response = login(self.client)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_user = {"id": self.user.id, "username": EMAIL}
        self.assertEqual(
            response.data,
            {"detail": "Login successful", "user": expected_user},
        )

    def test_sets_http_only_jwt_cookies(self):
        """Both tokens are set as HttpOnly cookies with their lifetime."""
        response = login(self.client)
        for name, lifetime in COOKIE_LIFETIMES.items():
            with self.subTest(cookie=name):
                cookie = response.cookies[name]
                self.assertTrue(cookie["httponly"])
                self.assertEqual(cookie["samesite"], "Lax")
                self.assertEqual(int(cookie["max-age"]), lifetime)

    def test_email_is_case_insensitive(self):
        """The email can be typed in any case."""
        response = login(self.client, email="MAX@Example.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_account_can_log_in_with_its_email(self):
        """The superuser from the .env can use the frontend as well."""
        User.objects.create_superuser("admin", "admin@example.com", PASSWORD)
        response = login(self.client, email="admin@example.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "admin")

    def test_wrong_data_gets_general_message(self):
        """Wrong password, unknown email and bad input look the same."""
        attempts = [
            {"email": EMAIL, "password": "falsch"},
            {"email": "niemand@example.com", "password": PASSWORD},
            {"email": "keine-mail"},
        ]
        for data in attempts:
            with self.subTest(data=data):
                response = self.client.post(LOGIN_URL, data, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data, INVALID_INPUT)
                self.assertNotIn("access_token", response.cookies)

    def test_inactive_account_gets_hint_only_with_correct_password(self):
        """Only the owner of an inactive account sees the activation hint."""
        create_user("neu@example.com", is_active=False)
        response = login(self.client, email="neu@example.com")
        self.assertEqual(response.data["detail"], ACCOUNT_NOT_ACTIVE_MESSAGE)
        response = login(self.client, "neu@example.com", "falsch")
        self.assertEqual(response.data["detail"], INVALID_INPUT_MESSAGE)
