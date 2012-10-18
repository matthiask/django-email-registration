from django.contrib.auth.models import User
from django.contrib.sites.models import get_current_site
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template.loader import TemplateDoesNotExist, render_to_string
from django.utils.translation import ugettext as _


def get_signer():
    """
    Returns the signer instance used to sign and unsign the registration
    link tokens
    """
    return signing.TimestampSigner(salt='email_registration')


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
    url = reverse('email_registration_confirm', kwargs={
        'code': get_signer().sign(u'%s-%s' % (email, user.id if user else '')),
        })

    url = '%s://%s%s' % (
        request.is_secure() and 'https' or 'http',
        get_current_site(request).domain,
        url)

    render_to_mail('registration/email_registration_email', {
        'url': url,
        },
        to=[email],
        ).send()


class InvalidCode(Exception):
    """Problems occurred during decoding the registration link"""
    pass


def decode(code, max_age=1800):
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
            _('The link is expired. Please request another registration link.')
            )

    except signing.BadSignature:
        raise InvalidCode(
            _('Unable to verify the signature. Please request a new'
                ' registration link.'))

    parts = data.rsplit('-', 1)
    email = parts[0]
    if len(parts) == 2 and parts[1]:
        try:
            user = User.objects.get(pk=parts[1])
        except (User.DoesNotExist, TypeError, ValueError):
            raise InvalidCode(
                _('Something went wrong while decoding the'
                    ' registration request. Please try again.'))
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
    lines = render_to_string('%s.txt' % template, context).splitlines()

    message = EmailMultiAlternatives(
        subject=lines[0],
        body=u'\n'.join(lines[2:]),
        **kwargs)

    try:
        message.attach_alternative(
            render_to_string('%s.html' % template, context),
            'text/html')
    except TemplateDoesNotExist:
        pass

    return message
