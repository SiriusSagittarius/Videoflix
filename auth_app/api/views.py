import django_rq
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.serializers import RegistrationSerializer
from auth_app.tokens import account_activation_token
from auth_app.utils import get_user_from_link, send_activation_email

INVALID_INPUT = {"detail": "Please check your input and try again."}
ACTIVATION_FAILED = {"message": "Activation failed."}


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
