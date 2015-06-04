# coding: utf-8
from __future__ import absolute_import, unicode_literals
import re
from django.contrib.auth.models import User
from django.core import mail

from django.test import TestCase, RequestFactory
from django.conf import settings
from django.utils.http import urlunquote
from email_registration.utils import get_confirmation_url, decode


class RedirectTest(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.email = 'test@example.com'

    def test_url_encoder(self):
        user = User.objects.create(
            username='test',
        )
        request = self.factory.post('/er/')
        url = get_confirmation_url(self.email, request)
        self.assertIn('http://testserver/er/test@example.com::::', url)

        url = get_confirmation_url(self.email, request, next='/foo/')
        self.assertIn('http://testserver/er/test@example.com:::/foo/:', url)

        url = get_confirmation_url(self.email, request, user=user)
        self.assertTrue(re.match(
            r'http://testserver/er/test@example.com:\d+:0::\w+:',
            url))

        url = get_confirmation_url(self.email, request,
                                   user=user, next='/foo/')
        self.assertTrue(re.match(
            r'http://testserver/er/test@example.com:\d+:0:/foo/:\w+:',
            url))

    def test_url_decode(self):
        user = User.objects.create(
            username='test',
        )
        request = self.factory.post('/er/')

        url = get_confirmation_url(self.email, request)
        match = re.search(r'http://testserver/er/(.+)/$', url)
        code = match.groups()[0]
        self.assertEqual((self.email, None, ''), decode(code))

        url = get_confirmation_url(self.email, request, next='/foo/')
        match = re.search(r'http://testserver/er/(.+)/$', url)
        code = match.groups()[0]
        self.assertEqual((self.email, None, '/foo/'), decode(code))

        url = get_confirmation_url(self.email, request, user=user)
        match = re.search(r'http://testserver/er/(.+)/$', url)
        code = match.groups()[0]
        self.assertEqual((self.email, user, ''), decode(code))

        url = get_confirmation_url(self.email, request, user=user,
                                   next='/foo/')
        match = re.search(r'http://testserver/er/(.+)/$', url)
        code = match.groups()[0]
        self.assertEqual((self.email, user, '/foo/'), decode(code))

    def test_default_redirect(self):
        request = self.factory.post('/er/')
        url = get_confirmation_url(self.email, request)

        response = self.client.post(url, {
            'new_password1': 'pass',
            'new_password2': 'pass',
        })
        self.assertRedirects(response, '/ac/login/')
        # django auth login
        response = self.client.post('/ac/login/', {
            'username': 'test@example.com',
            'password': 'pass',
        })
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

    def test_custom_redirect(self):
        response = self.client.post('/er/', {
            'email': 'test@example.com',
            'next': '/foo/bar/'
        })
        self.assertContains(
            response,
            'We sent you an email to test@example.com.')

        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        url = urlunquote(
            [line for line in body.splitlines() if 'testserver' in line][0])
        self.assertTrue(
            'http://testserver/er/test@example.com:::/foo/bar/:' in url)
        response = self.client.get(url)
        self.assertContains(response, 'id="id_new_password2"')

        response = self.client.post(url, {
            'new_password1': 'pass',
            'new_password2': 'pass',
        })
        self.assertRedirects(response, '/ac/login/?next=/foo/bar/')
