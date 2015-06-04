import re
import time

from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import timezone
from django.utils.http import urlunquote

from email_registration.utils import get_signer, send_registration_mail


def _messages(response):
    return [m.message for m in response.context['messages']]


class RegistrationTest(TestCase):
    """ Functional tests for the registration process """
    def test_registration(self):
        self.assertFalse(User.objects.filter(
            email='test@example.com').exists())
        response = self.client.get('/er/')

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response['Allow'], 'POST')

        response = self.client.post('/er/', {
            'email': 'test@example.com',
        })
        self.assertContains(
            response,
            'We sent you an email to test@example.com.')

        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        url = urlunquote(
            [line for line in body.splitlines() if 'testserver' in line][0])
        self.assertTrue('http://testserver/er/test@example.com::::' in url)

        response = self.client.get(url)
        self.assertContains(response, 'id="id_new_password2"')

        response = self.client.post(url, {
            'new_password1': 'pass',
            'new_password2': 'passss',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(
            email='test@example.com').exists())

        response = self.client.post(url, {
            'new_password1': 'pass',
            'new_password2': 'pass',
        })
        self.assertRedirects(response, '/ac/login/')

        user = User.objects.get()
        self.assertEqual(user.username, 'test@example.com')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.is_active, True)

        # django auth login
        response = self.client.post('/ac/login/', {
            'username': 'test@example.com',
            'password': 'pass',
        })
        self.assertRedirects(response, '/?login=1')

    def test_existing_user(self):
        user = User.objects.create(
            username='test',
        )

        request = RequestFactory().get('/')
        send_registration_mail('test@example.com', request, user=user)

        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        url = urlunquote(
            [line for line in body.splitlines() if 'testserver' in line][0])
        self.assertTrue(re.match(
            r'http://testserver/er/test@example.com:\d+:0::\w+:',
            url))

        response = self.client.get(url)

        self.assertContains(response, 'id="id_new_password2"')

        response = self.client.post(url, {
            'new_password1': 'pass',
            'new_password2': 'pass',
        })
        self.assertRedirects(response, '/ac/login/')

        user = User.objects.get()
        self.assertEqual(user.username, 'test')
        self.assertEqual(user.email, '')
        self.assertTrue(user.check_password('pass'))

        time.sleep(1.1)
        user.last_login = timezone.now()
        user.save()

        response = self.client.get(url, follow=True)
        self.assertEqual(
            _messages(response),
            ['The link has already been used.'])
        self.assertRedirects(response, '/')

        response = self.client.get(
            url.replace('/er/', '/er-quick/', 1),
            follow=True,
        )
        self.assertEqual(
            _messages(response),
            ['The link is expired. Please request another registration link.'])

        response = self.client.get(
            url.replace('com:', 'ch:', 1),
            follow=True,
        )
        self.assertEqual(
            _messages(response),
            [
                'Unable to verify the signature.'
                ' Please request a new registration link.'
            ])

        user.delete()
        response = self.client.get(url, follow=True)
        self.assertEqual(
            _messages(response),
            [
                'Something went wrong while decoding the'
                ' registration request. Please try again.'
            ])

    def test_already_existing_email(self):
            user = User.objects.create(
                username='test@example.com',
                email='test@example.com',
            )
            response = self.client.post('/er/', {
                'email': user.email,
            })
            self.assertContains(
                response,
                'Did you want to reset your password?',
                status_code=200)

    def test_user_created_in_the_meantime(self):
        response = self.client.post('/er/', {
            'email': 'test@example.com',
        })
        self.assertContains(
            response,
            'We sent you an email to test@example.com.')

        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        url = urlunquote(
            [line for line in body.splitlines() if 'testserver' in line][0])

        self.assertTrue('http://testserver/er/test@example.com:::' in url)

        User.objects.create_user('test', 'test@example.com', 'blaa')

        response = self.client.get(url, follow=True)
        self.assertEqual(
            _messages(response),
            [
                'This email address already exists as an account.'
                ' Did you want to reset your password?'
            ])

    def test_crap(self):
        user = User.objects.create_user('test', 'test@example.com', 'pass')

        code = [
            user.email,
            str(user.id),
            # Intentionally forget the timestamp.
        ]

        url = reverse(
            'email_registration_confirm',
            kwargs={
                'code': get_signer().sign(u':'.join(code)),
            })

        response = self.client.get(url, follow=True)
        self.assertEqual(
            _messages(response),
            [
                'Something went wrong while decoding the'
                ' registration request. Please try again.'
            ])
