from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.tests.helpers import build_link_url, create_user
from auth_app.tokens import account_activation_token


class ActivationTests(APITestCase):
    """GET /api/activate/<uidb64>/<token>/"""

    def setUp(self):
        """Create an inactive user and the URL of its activation link."""
        self.user = create_user(is_active=False)
        self.url = build_link_url(
            "activate", self.user, account_activation_token
        )

    def test_activates_account(self):
        """A valid link activates the account."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data, {"message": "Account successfully activated."}
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_link_works_only_once(self):
        """After the activation the same link is no longer valid."""
        self.client.get(self.url)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"message": "Activation failed."})

    def test_rejects_invalid_links(self):
        """Wrong tokens, broken uids and unknown users are rejected."""
        uid = self.url.split("/")[3]
        urls = [
            f"/api/activate/{uid}/abc-123/",
            "/api/activate/!!!/abc-123/",
            "/api/activate/OTk5OQ/abc-123/",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
