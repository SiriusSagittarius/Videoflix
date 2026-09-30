from email.message import MIMEPart
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from auth_app.tokens import account_activation_token

ACCESS_TOKEN_COOKIE = "access_token"
EMAIL_TEMPLATE_DIR = "auth_app/emails"
LOGO_CID = "videoflix_logo"
LOGO_PATH = (
    Path(__file__).resolve().parent
    / "static" / "auth_app" / "images" / "videoflix_logo.png"
)


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
