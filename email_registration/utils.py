from django.contrib.auth.models import User
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.template.loader import TemplateDoesNotExist, render_to_string
from django.utils.http import int_to_base36
from django.utils.translation import gettext as _


try:
    from django.urls import reverse
except ImportError:  # pragma: no cover
    from django.core.urlresolvers import reverse


def get_signer(salt="email_registration"):
    """
    Returns the signer instance used to sign and unsign the registration
    link tokens
    """
    return signing.TimestampSigner(salt=salt)


def get_last_login_timestamp(user):
    """
    Django 1.7 allows the `last_login` timestamp to be `None` for new users.
    """
    return int(user.last_login.strftime("%s")) if user.last_login else 0


def get_confirmation_url(email, request, user=None):
    """
    Returns the confirmation URL
    """
    code = [email, "", ""]
    if user:
        code[1] = str(user.id)
        code[2] = int_to_base36(get_last_login_timestamp(user))

    return request.build_absolute_uri(
        reverse(
            "email_registration_confirm",
            kwargs={
                "code": get_signer().sign(":".join(code)),
            },
        )
    )


def send_registration_mail(email, request, user=None):
    """
    Sends the registration mail

    * ``email``: The email address where the registration link should be
      sent to.
    * ``request``: A HTTP request instance, used to construct the complete
      URL (including protocol and domain) for the registration link.
    * ``user``: Optional user instance. If the user exists already and you
      just want to send a link where the user can choose his/her password.

    The mail is rendered using the following two templates:

    * ``registration/email_registration_email.txt``: The first line of this
      template will be the subject, the third to the last line the body of the
      email.
    * ``registration/email_registration_email.html``: The body of the HTML
      version of the mail. This template is **NOT** available by default and
      is not required either.
    """

    render_to_mail(
        "registration/email_registration_email",
        {
            "url": get_confirmation_url(email, request, user=user),
        },
        to=[email],
    ).send()


class InvalidCode(Exception):
    """Problems occurred during decoding the registration link"""

    pass


def decode(code, max_age=3 * 86400):
    """
    Decodes the code from the registration link and returns a tuple consisting
    of the verified email address and the associated user instance or ``None``
    if no user was passed to ``send_registration_mail``

    This method raises ``InvalidCode`` exceptions containing an translated
    message what went wrong suitable for presenting directly to the user.
    """
    try:
        data = get_signer().unsign(code, max_age=max_age)
    except signing.SignatureExpired:
        raise InvalidCode(
            _("The link is expired. Please request another registration link.")
        )

    except signing.BadSignature:
        raise InvalidCode(
            _(
                "Unable to verify the signature. Please request a new"
                " registration link."
            )
        )

    parts = data.rsplit(":", 2)
    if len(parts) != 3:
        raise InvalidCode(
            _(
                "Something went wrong while decoding the"
                " registration request. Please try again."
            )
        )

    email, uid, timestamp = parts
    if uid and timestamp:
        try:
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, TypeError, ValueError):
            raise InvalidCode(
                _(
                    "Something went wrong while decoding the"
                    " registration request. Please try again."
                )
            )

        if timestamp != int_to_base36(get_last_login_timestamp(user)):
            raise InvalidCode(_("The link has already been used."))

    else:
        user = None

    return email, user


def render_to_mail(template, context, **kwargs):
    """
    Renders a mail and returns the resulting ``EmailMultiAlternatives``
    instance

    * ``template``: The base name of the text and HTML (optional) version of
      the mail.
    * ``context``: The context used to render the mail. This context instance
      should contain everything required.
    * Additional keyword arguments are passed to the ``EmailMultiAlternatives``
      instantiation. Use those to specify the ``to``, ``headers`` etc.
      arguments.

    Usage example::

        # Render the template myproject/hello_mail.txt (first line contains
        # the subject, third to last the body) and optionally the template
        # myproject/hello_mail.html containing the alternative HTML
        # representation.
        message = render_to_mail('myproject/hello_mail', {}, to=[email])
        message.send()
    """
    lines = iter(render_to_string("%s.txt" % template, context).splitlines())

    subject = ""
    while True:
        line = next(lines)
        if line:
            subject = line
            break

    body = "\n".join(lines).strip("\n")
    message = EmailMultiAlternatives(subject=subject, body=body, **kwargs)

    try:
        message.attach_alternative(
            render_to_string("%s.html" % template, context), "text/html"
        )
    except TemplateDoesNotExist:
        pass

    return message
