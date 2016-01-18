from django.conf.urls import url

from email_registration.views import (
    email_registration_form, email_registration_confirm
)


urlpatterns = [
    url(
        r'^$',
        email_registration_form,
        name='email_registration_form',
    ),
    url(
        r'^(?P<code>[^/]+)/$',
        email_registration_confirm,
        name='email_registration_confirm',
    ),
]
