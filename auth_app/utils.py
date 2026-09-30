from email.message import MIMEPart
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.tokens import account_activation_token

ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
INVALID_INPUT_MESSAGE = "Please check your input and try again."
ACCOUNT_NOT_ACTIVE_MESSAGE = (
    "Please activate your account first. "
    "Check your emails for the activation link."
)
EMAIL_TEMPLATE_DIR = "auth_app/emails"
LOGO_CID = "videoflix_logo"
LOGO_PATH = (
    Path(__file__).resolve().parent
    / "static" / "auth_app" / "images" / "videoflix_logo.png"
)


def find_user_by_credentials(email, password):
    """Return the user with this email and password, active or not.

    The password is hashed for unknown emails as well, so the response
    time does not reveal which email addresses are registered.
    """
    user = User.objects.filter(username=email).first()
    if user is None:
        User().set_password(password)
        return None
    return user if user.check_password(password) else None


def get_login_error(errors):
    """Return the login error, general unless the account is inactive."""
    messages = errors.get("non_field_errors", [INVALID_INPUT_MESSAGE])
    return messages[0]


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


def set_access_cookie(response, access_token):
    """Store the access token in its HttpOnly cookie."""
    set_token_cookie(
        response, ACCESS_TOKEN_COOKIE, access_token,
        api_settings.ACCESS_TOKEN_LIFETIME,
    )


def set_auth_cookies(response, user):
    """Create a token pair for the user and store both tokens as cookies."""
    refresh_token = RefreshToken.for_user(user)
    set_access_cookie(response, refresh_token.access_token)
    set_token_cookie(
        response, REFRESH_TOKEN_COOKIE, refresh_token,
        api_settings.REFRESH_TOKEN_LIFETIME,
    )


def delete_auth_cookies(response):
    """Remove both JWT cookies from the browser."""
    for name in (ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE):
        response.delete_cookie(name, samesite="Lax")


def create_access_token(raw_refresh_token):
    """Return a new access token for a valid refresh token, else None."""
    try:
        return RefreshToken(raw_refresh_token).access_token
    except TokenError:
        return None


def blacklist_refresh_token(raw_token):
    """Put a refresh token on the blacklist, invalid tokens are skipped."""
    try:
        RefreshToken(raw_token).blacklist()
    except TokenError:
        return


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


def get_active_user_by_email(email):
    """Return the active user with this email address or None."""
    return User.objects.filter(email__iexact=email, is_active=True).first()


def send_password_reset_email(user_id):
    """Send the password reset email to the user with this id."""
    user = User.objects.get(pk=user_id)
    token = default_token_generator.make_token(user)
    link = build_frontend_link("confirm_password.html", user, token)
    context = {"reset_link": link}
    send_html_email(
        "Reset your Password", "password_reset_email", context, user.email
    )
