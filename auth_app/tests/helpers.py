import re

from django.contrib.auth.models import User
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

PASSWORD = "Sicheres-Passwort-1"
EMAIL = "max@example.com"


def create_user(email=EMAIL, is_active=True):
    """Create a user like the registration does, the email is the username."""
    return User.objects.create_user(
        email, email, PASSWORD, is_active=is_active
    )


def build_link_url(endpoint, user, token_generator):
    """Return the API URL of an email link for this user."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"/api/{endpoint}/{uid}/{token_generator.make_token(user)}/"


def login(client, email=EMAIL, password=PASSWORD):
    """Log the test client in, it keeps the JWT cookies afterwards."""
    data = {"email": email, "password": password}
    return client.post("/api/login/", data, format="json")


def find_link_data(text):
    """Return uid and token from the link in an email text."""
    return re.search(r"uid=([^&]+)&token=(\S+)", text).groups()
