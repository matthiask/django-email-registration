from datetime import timedelta
import httplib
import re

from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import timezone

from email_registration.signals import password_set
from email_registration.utils import send_registration_mail


class RegistrationTest(TestCase):
    def test_registration(self):
        response = self.client.get('/er/')

        self.assertEqual(response.status_code, httplib.METHOD_NOT_ALLOWED)
        self.assertEqual(response['Allow'], 'POST')

        response = self.client.post('/er/', {
            'email': 'test@example.com',
            })
        self.assertContains(response,
            'We sent you an e-mail to test@example.com.')

        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        url = [line for line in body.splitlines() if 'testserver' in line][0]

        self.assertTrue('http://testserver/er/test@example.com:::' in url)

        response = self.client.get(url)
        self.assertContains(response, 'id="id_new_password2"')

        response = self.client.post(url, {
            'new_password1': 'pass',
            'new_password2': 'pass',
            })
        self.assertRedirects(response, '/ac/login/')

        user = User.objects.get()
        self.assertEqual(user.username, 'test@example.com')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.is_active, True)

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
        url = [line for line in body.splitlines() if 'testserver' in line][0]

        self.assertTrue(re.match(
            r'http://testserver/er/test@example.com:\d+:\w+:',
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
