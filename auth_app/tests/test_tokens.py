from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from auth_app.tests.helpers import create_user, login

LOGOUT_MESSAGE = (
    "Logout successful! All tokens will be deleted. "
    "Refresh token is now invalid."
)


class LogoutTests(APITestCase):
    """POST /api/logout/"""

    def setUp(self):
        """Log a user in, so the client holds both cookies."""
        create_user()
        login(self.client)

    def assert_cookies_deleted(self, response):
        """Check that the answer tells the browser to delete both cookies."""
        for name in ("access_token", "refresh_token"):
            self.assertEqual(int(response.cookies[name]["max-age"]), 0)

    def test_blacklists_refresh_token_and_deletes_cookies(self):
        """After the logout the refresh token cannot be used any more."""
        refresh_token = self.client.cookies["refresh_token"].value
        response = self.client.post("/api/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], LOGOUT_MESSAGE)
        self.assert_cookies_deleted(response)
        with self.assertRaises(TokenError):
            RefreshToken(refresh_token)

    def test_without_cookie_returns_400(self):
        """Without a refresh cookie the logout fails, cookies are cleared."""
        self.client.cookies.clear()
        response = self.client.post("/api/logout/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Refresh token is missing.")
        self.assert_cookies_deleted(response)

    def test_invalid_token_still_deletes_cookies(self):
        """A broken refresh token does not stop the logout."""
        self.client.cookies["refresh_token"] = "kaputt"
        response = self.client.post("/api/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_cookies_deleted(response)


class TokenRefreshTests(APITestCase):
    """POST /api/token/refresh/"""

    def setUp(self):
        """Log a user in, so the client holds both cookies."""
        self.user = create_user()
        login(self.client)

    def test_sets_new_access_cookie(self):
        """A valid refresh cookie leads to a new access token cookie."""
        response = self.client.post("/api/token/refresh/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Token refreshed")
        new_token = response.cookies["access_token"].value
        self.assertEqual(new_token, response.data["access"])
        self.assertEqual(AccessToken(new_token)["user_id"], str(self.user.id))

    def test_without_cookie_returns_400(self):
        """Without a refresh cookie there is no new token."""
        self.client.cookies.clear()
        response = self.client.post("/api/token/refresh/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_token_returns_401(self):
        """A broken refresh token is rejected."""
        self.client.cookies["refresh_token"] = "kaputt"
        response = self.client.post("/api/token/refresh/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_from_before_the_logout_returns_401(self):
        """A blacklisted refresh token cannot create new access tokens."""
        refresh_token = self.client.cookies["refresh_token"].value
        self.client.post("/api/logout/")
        self.client.cookies["refresh_token"] = refresh_token
        response = self.client.post("/api/token/refresh/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
