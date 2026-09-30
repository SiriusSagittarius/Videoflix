import django_rq
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.serializers import LoginSerializer, RegistrationSerializer
from auth_app.tokens import account_activation_token
from auth_app.utils import (
    INVALID_INPUT_MESSAGE,
    REFRESH_TOKEN_COOKIE,
    blacklist_refresh_token,
    create_access_token,
    delete_auth_cookies,
    get_login_error,
    get_user_from_link,
    send_activation_email,
    set_access_cookie,
    set_auth_cookies,
)

INVALID_INPUT = {"detail": INVALID_INPUT_MESSAGE}
ACTIVATION_FAILED = {"message": "Activation failed."}
REFRESH_MISSING = {"detail": "Refresh token is missing."}
REFRESH_INVALID = {"detail": "Refresh token is invalid."}
LOGOUT_SUCCESS = {
    "detail": "Logout successful! All tokens will be deleted. "
              "Refresh token is now invalid."
}


class RegistrationView(APIView):
    """Register a new user whose account stays inactive until activation."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Create the user and return its data and the activation token."""
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(INVALID_INPUT, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        django_rq.enqueue(send_activation_email, user.pk)
        response_data = {
            "user": {"id": user.id, "email": user.email},
            "token": account_activation_token.make_token(user),
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class ActivationView(APIView):
    """Activate an account with the uid and token from the activation link."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        """Set the user active if the token is valid."""
        user = get_user_from_link(uidb64, token, account_activation_token)
        if user is None:
            return Response(
                ACTIVATION_FAILED, status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response({"message": "Account successfully activated."})


class LoginView(APIView):
    """Log a user in and set the JWT cookies."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Check the login data and answer with user data and cookies."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            error = {"detail": get_login_error(serializer.errors)}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.validated_data["user"]
        response = Response({
            "detail": "Login successful",
            "user": {"id": user.id, "username": user.username},
        })
        set_auth_cookies(response, user)
        return response


class LogoutView(APIView):
    """Log a user out by invalidating the refresh token.

    Works without a valid access token, so an expired login can still
    be ended cleanly.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Blacklist the refresh token and delete both JWT cookies."""
        refresh_token = request.COOKIES.get(REFRESH_TOKEN_COOKIE)
        if refresh_token is None:
            response = Response(REFRESH_MISSING, status.HTTP_400_BAD_REQUEST)
        else:
            blacklist_refresh_token(refresh_token)
            response = Response(LOGOUT_SUCCESS)
        delete_auth_cookies(response)
        return response


class CookieTokenRefreshView(APIView):
    """Issue a new access token based on the refresh token cookie."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Set a new access token cookie if the refresh token is valid."""
        refresh_token = request.COOKIES.get(REFRESH_TOKEN_COOKIE)
        if refresh_token is None:
            return Response(REFRESH_MISSING, status.HTTP_400_BAD_REQUEST)
        access_token = create_access_token(refresh_token)
        if access_token is None:
            return Response(REFRESH_INVALID, status.HTTP_401_UNAUTHORIZED)
        data = {"detail": "Token refreshed", "access": str(access_token)}
        response = Response(data)
        set_access_cookie(response, access_token)
        return response
