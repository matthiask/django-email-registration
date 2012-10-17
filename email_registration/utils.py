from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string


def get_signer():
    return signing.TimestampSigner(salt='email_registration')


def send_registration_mail(email, user_pk=None, request=None):
    url = reverse('email_registration_confirm', kwargs={
        'code': get_signer().sign(u'%s-%s' % (email, user_pk or '')),
        })

    if request:
        url = request.build_absolute_uri(url)

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
