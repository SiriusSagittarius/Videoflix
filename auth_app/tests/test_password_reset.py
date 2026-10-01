from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.tests.helpers import PASSWORD, build_link_url, create_user
from auth_app.utils import INVALID_INPUT_MESSAGE, send_password_reset_email

RESET_URL = "/api/password_reset/"
RESET_SENT = {"detail": "An email has been sent to reset your password."}
INVALID_INPUT = {"detail": INVALID_INPUT_MESSAGE}
NEW_PASSWORD = "Neues-Passwort-2"


def password_data(new_password, confirm_password=None):
    """Return the request body of the frontend form for a new password."""
    return {
        "new_password": new_password,
        "confirm_password": confirm_password or new_password,
    }


@patch("django_rq.get_queue")
class PasswordResetTests(APITestCase):
    """POST /api/password_reset/"""

    def test_queues_email_for_active_user(self, get_queue):
        """An active user gets the reset email, any letter case works."""
        user = create_user()
        data = {"email": "MAX@example.com"}
        response = self.client.post(RESET_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, RESET_SENT)
        get_queue.assert_called_once_with("emails")
        get_queue.return_value.enqueue.assert_called_once_with(
            send_password_reset_email, user.pk
        )

    def test_same_answer_for_unknown_or_inactive_users(self, get_queue):
        """Nobody can find out which emails are registered."""
        create_user("neu@example.com", is_active=False)
        for email in ("neu@example.com", "niemand@example.com"):
            with self.subTest(email=email):
                data = {"email": email}
                response = self.client.post(RESET_URL, data, format="json")
                self.assertEqual(response.data, RESET_SENT)
        get_queue.assert_not_called()

    def test_rejects_invalid_email(self, get_queue):
        """An invalid email is a bad request."""
        data = {"email": "keine-mail"}
        response = self.client.post(RESET_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordConfirmTests(APITestCase):
    """POST /api/password_confirm/<uidb64>/<token>/"""

    def setUp(self):
        """Create a user and the URL of its password reset link."""
        self.user = create_user()
        self.url = build_link_url(
            "password_confirm", self.user, default_token_generator
        )

    def test_sets_new_password(self):
        """The new password replaces the old one."""
        data = password_data(NEW_PASSWORD)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "Your Password has been successfully reset.",
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))
        self.assertFalse(self.user.check_password(PASSWORD))

    def test_link_works_only_once(self):
        """After a password change the same link is no longer valid."""
        self.client.post(self.url, password_data(NEW_PASSWORD), format="json")
        data = password_data("Noch-Ein-Passwort-3")
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "The reset link is invalid or has expired.",
        )

    def test_rejects_invalid_passwords(self):
        """Different, weak or email-like passwords change nothing."""
        cases = [
            password_data(NEW_PASSWORD, "Anderes-Passwort-9"),
            password_data("12345678"),
            password_data("maxexample"),
        ]
        for data in cases:
            with self.subTest(data=data):
                response = self.client.post(self.url, data, format="json")
                self.assertEqual(response.data, INVALID_INPUT)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))
