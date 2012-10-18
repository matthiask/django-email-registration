from django.contrib.auth.models import User
from django.contrib.sites.models import get_current_site
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _


def get_signer():
    return signing.TimestampSigner(salt='email_registration')


def send_registration_mail(email, request, user=None):
    url = reverse('email_registration_confirm', kwargs={
        'code': get_signer().sign(u'%s-%s' % (email, user.id if user else '')),
        })

    url = '%s://%s%s' % (
        request.is_secure() and 'https' or 'http',
        get_current_site(request).domain,
        url)

    lines = render_to_string('registration/email_registration_email.txt', {
        'url': url,
        }).splitlines()

    message = EmailMultiAlternatives(
        subject=lines[0],
        body=u'\n'.join(lines[2:]),
        to=[email],
        headers={
            #'Reply-To': 'TODO something sane',
            },
        )
    message.send()


class InvalidCode(Exception):
    pass


def decode(code):
    try:
        data = get_signer().unsign(code, max_age=1800)
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
