from rest_framework_simplejwt.authentication import JWTAuthentication

from auth_app.utils import ACCESS_TOKEN_COOKIE


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate a request with the JWT stored in the access token cookie."""

    def authenticate(self, request):
        """Return (user, token) for a valid cookie or None if there is no cookie."""
        raw_token = request.COOKIES.get(ACCESS_TOKEN_COOKIE)
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
