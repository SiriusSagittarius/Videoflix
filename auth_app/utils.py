from email.message import MIMEPart
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.tokens import account_activation_token

ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
EMAIL_TEMPLATE_DIR = "auth_app/emails"
LOGO_CID = "videoflix_logo"
LOGO_PATH = (
    Path(__file__).resolve().parent
    / "static" / "auth_app" / "images" / "videoflix_logo.png"
)


def set_token_cookie(response, name, token, lifetime):
    """Store a token in an HttpOnly cookie that expires with the token."""
    response.set_cookie(
        name,
        str(token),
        max_age=int(lifetime.total_seconds()),
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
    )


def set_auth_cookies(response, user):
    """Create a token pair for the user and store both tokens as cookies."""
    refresh_token = RefreshToken.for_user(user)
    set_token_cookie(
        response, ACCESS_TOKEN_COOKIE, refresh_token.access_token,
        api_settings.ACCESS_TOKEN_LIFETIME,
    )
    set_token_cookie(
        response, REFRESH_TOKEN_COOKIE, refresh_token,
        api_settings.REFRESH_TOKEN_LIFETIME,
    )


def get_user_by_uid(uidb64):
    """Return the user for a base64 encoded id or None if it is invalid."""
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def get_user_from_link(uidb64, token, token_generator):
    """Return the user of an email link if uid and token are valid."""
    user = get_user_by_uid(uidb64)
    if user is not None and token_generator.check_token(user, token):
        return user
    return None


def build_frontend_link(page, user, token):
    """Return the link to a frontend auth page with uid and token."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{settings.FRONTEND_URL}/pages/auth/{page}?uid={uid}&token={token}"


def create_logo_part():
    """Return the Videoflix logo as an inline image for HTML emails."""
    logo = MIMEPart()
    logo.set_content(
        LOGO_PATH.read_bytes(),
        maintype="image",
        subtype="png",
        disposition="inline",
        cid=f"<{LOGO_CID}>",
    )
    return logo


def send_html_email(subject, template_name, context, recipient):
    """Send an email with a plain text and an HTML version and the logo."""
    context = {**context, "logo_cid": LOGO_CID}
    template_path = f"{EMAIL_TEMPLATE_DIR}/{template_name}"
    message = EmailMultiAlternatives(
        subject=subject,
        body=render_to_string(f"{template_path}.txt", context),
        to=[recipient],
    )
    message.attach_alternative(
        render_to_string(f"{template_path}.html", context), "text/html"
    )
    message.attach(create_logo_part())
    message.send()


def send_activation_email(user_id):
    """Send the account activation email to the user with this id."""
    user = User.objects.get(pk=user_id)
    token = account_activation_token.make_token(user)
    context = {
        "user": user,
        "activation_link": build_frontend_link("activate.html", user, token),
    }
    send_html_email(
        "Confirm your email", "activation_email", context, user.email
    )
