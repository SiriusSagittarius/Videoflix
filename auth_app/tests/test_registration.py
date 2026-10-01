from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.tests.helpers import EMAIL, PASSWORD, create_user
from auth_app.tokens import account_activation_token
from auth_app.utils import INVALID_INPUT_MESSAGE, send_activation_email

URL = "/api/register/"
INVALID_INPUT = {"detail": INVALID_INPUT_MESSAGE}


def registration_data(email=EMAIL, password=PASSWORD, confirmed=None):
    """Return the request body the frontend sends for a sign-up."""
    return {
        "email": email,
        "password": password,
        "confirmed_password": confirmed or password,
        "privacy_policy": "on",
    }


@patch("django_rq.get_queue")
class RegistrationTests(APITestCase):
    """POST /api/register/"""

    def test_creates_inactive_user_and_queues_email(self, get_queue):
        """A valid sign-up creates an inactive user and queues the email."""
        response = self.client.post(URL, registration_data(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=EMAIL)
        self.assertFalse(user.is_active)
        self.assertEqual(user.username, EMAIL)
        self.assertTrue(user.check_password(PASSWORD))
        get_queue.assert_called_once_with("emails")
        get_queue.return_value.enqueue.assert_called_once_with(
            send_activation_email, user.pk
        )

    def test_returns_user_data_and_valid_token(self, get_queue):
        """The answer contains the user and a working activation token."""
        response = self.client.post(URL, registration_data(), format="json")
        user = User.objects.get(email=EMAIL)
        self.assertEqual(
            response.data["user"], {"id": user.id, "email": EMAIL}
        )
        token = response.data["token"]
        self.assertTrue(account_activation_token.check_token(user, token))

    def test_stores_email_in_lower_case(self, get_queue):
        """Emails are saved in lower case, so logins match later."""
        data = registration_data("Max@Example.COM")
        self.client.post(URL, data, format="json")
        self.assertTrue(User.objects.filter(username=EMAIL).exists())

    def test_rejects_registered_email_with_general_message(self, get_queue):
        """A taken email gets the general message, nothing is revealed."""
        create_user()
        data = registration_data("MAX@example.com")
        response = self.client.post(URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, INVALID_INPUT)
        get_queue.assert_not_called()

    def test_rejects_invalid_passwords(self, get_queue):
        """Different, weak or email-like passwords are rejected."""
        cases = [
            registration_data(confirmed="Anderes-Passwort-9"),
            registration_data(password="12345678"),
            registration_data("maxmustermann@example.com", "maxmustermann"),
        ]
        for data in cases:
            with self.subTest(data=data):
                response = self.client.post(URL, data, format="json")
                self.assertEqual(response.data, INVALID_INPUT)
        self.assertFalse(User.objects.exists())

    def test_rejects_missing_or_invalid_email(self, get_queue):
        """Without a valid email no user is created."""
        for data in ({"password": PASSWORD}, registration_data("keine-mail")):
            with self.subTest(data=data):
                response = self.client.post(URL, data, format="json")
                self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.exists())

    def test_ignores_broken_login_cookie(self, get_queue):
        """An old access cookie in the browser does not block a sign-up."""
        self.client.cookies["access_token"] = "abc.def.ghi"
        response = self.client.post(URL, registration_data(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
