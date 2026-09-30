from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Create activation link tokens that expire once the account is active."""

    key_salt = "auth_app.tokens.AccountActivationTokenGenerator"

    def _make_hash_value(self, user, timestamp):
        """Build the hash from user id, activation state and timestamp."""
        return f"{user.pk}{user.is_active}{timestamp}"


account_activation_token = AccountActivationTokenGenerator()
