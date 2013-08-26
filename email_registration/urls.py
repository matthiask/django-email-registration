from django.conf.urls import patterns, url


urlpatterns = patterns('email_registration.views',
    url(r'^$',
        'email_registration_form',
        name='email_registration_form'),
    url(r'^(?P<code>[^/]+)/$',
        'email_registration_confirm',
        name='email_registration_confirm'),
)
