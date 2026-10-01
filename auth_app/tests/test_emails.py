from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase

from auth_app.tests.helpers import create_user, find_link_data
from auth_app.tokens import account_activation_token
from auth_app.utils import (
    get_user_from_link,
    send_activation_email,
    send_password_reset_email,
)


def has_inline_logo(message):
    """Return True if the logo is embedded in the email."""
    parts = message.message().walk()
    return any(part.get("Content-ID") == "<videoflix_logo>" for part in parts)


class EmailTests(TestCase):
    """Activation and password reset emails."""

    def setUp(self):
        """Create a user who gets the emails."""
        self.user = create_user()

    def test_activation_email_has_text_html_and_logo(self):
        """The email has both versions, the logo and the frontend link."""
        send_activation_email(self.user.pk)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Confirm your email")
        self.assertEqual(message.to, [self.user.email])
        page = f"{settings.FRONTEND_URL}/pages/auth/activate.html?uid="
        self.assertIn(page, message.body)
        html = message.alternatives[0].content
        self.assertIn("cid:videoflix_logo", html)
        self.assertIn("Activate account", html)
        self.assertTrue(has_inline_logo(message))

    def test_activation_link_contains_valid_token(self):
        """The link in the email activates exactly this user."""
        send_activation_email(self.user.pk)
        uid, token = find_link_data(mail.outbox[0].body)
        user = get_user_from_link(uid, token, account_activation_token)
        self.assertEqual(user, self.user)

    def test_password_reset_email_links_to_confirm_page(self):
        """The reset email leads to the frontend page with a valid token."""
        send_password_reset_email(self.user.pk)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Reset your Password")
        self.assertIn("/pages/auth/confirm_password.html?uid=", message.body)
        self.assertIn("Reset password", message.alternatives[0].content)
        uid, token = find_link_data(message.body)
        user = get_user_from_link(uid, token, default_token_generator)
        self.assertEqual(user, self.user)
