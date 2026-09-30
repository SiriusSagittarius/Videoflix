from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from rest_framework import serializers

from auth_app.utils import (
    ACCOUNT_NOT_ACTIVE_MESSAGE,
    INVALID_INPUT_MESSAGE,
    find_user_by_credentials,
)


class RegistrationSerializer(serializers.Serializer):
    """Validate the sign-up data and create an inactive user."""

    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(write_only=True)
    confirmed_password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        """Reject email addresses that are already registered."""
        email = value.lower()
        email_taken = Q(email__iexact=email) | Q(username__iexact=email)
        if User.objects.filter(email_taken).exists():
            raise serializers.ValidationError("Email is already registered.")
        return email

    def validate(self, attrs):
        """Check that both passwords match and are strong enough."""
        if attrs["password"] != attrs["confirmed_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        """Create an inactive user with the email as username."""
        email = validated_data["email"]
        return User.objects.create_user(
            username=email,
            email=email,
            password=validated_data["password"],
            is_active=False,
        )


class LoginSerializer(serializers.Serializer):
    """Check the login data of an active user."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Attach the user if email and password belong to an active user."""
        user = find_user_by_credentials(
            attrs["email"].lower(), attrs["password"]
        )
        if user is None:
            raise serializers.ValidationError(INVALID_INPUT_MESSAGE)
        if not user.is_active:
            raise serializers.ValidationError(ACCOUNT_NOT_ACTIVE_MESSAGE)
        attrs["user"] = user
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """Validate the email address for a password reset request."""

    email = serializers.EmailField()


class PasswordConfirmSerializer(serializers.Serializer):
    """Validate the new password from the password reset form."""

    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Check that both passwords match and are strong enough."""
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(attrs["new_password"], self.context.get("user"))
        return attrs
