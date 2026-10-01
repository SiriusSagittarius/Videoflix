from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import AccessToken

from auth_app.api.authentication import CookieJWTAuthentication
from auth_app.tests.helpers import create_user


class CookieJWTAuthenticationTests(TestCase):
    """Authentication with the access token cookie."""

    def setUp(self):
        """Create a user and the authentication class."""
        self.user = create_user()
        self.authentication = CookieJWTAuthentication()

    def build_request(self, access_token=None):
        """Return a request that carries the given access token cookie."""
        request = APIRequestFactory().get("/api/video/")
        if access_token is not None:
            request.COOKIES["access_token"] = access_token
        return request

    def test_returns_none_without_cookie(self):
        """Without a cookie the user is simply not logged in."""
        result = self.authentication.authenticate(self.build_request())
        self.assertIsNone(result)

    def test_returns_user_for_valid_cookie(self):
        """A valid token in the cookie identifies the user."""
        token = str(AccessToken.for_user(self.user))
        user, _ = self.authentication.authenticate(self.build_request(token))
        self.assertEqual(user, self.user)

    def test_rejects_broken_cookie(self):
        """A broken token is rejected with an error."""
        with self.assertRaises(InvalidToken):
            self.authentication.authenticate(self.build_request("a.b.c"))
