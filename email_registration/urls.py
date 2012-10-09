from django.conf.urls import patterns, include, url


urlpatterns = patterns('email_registration.views',
    url(r'^$',
        'email_registration_form',
        name='email_registration_form'),
    url(r'^confirm/(?P<code>[-\w]+)/$',
        'email_registration_confirm',
        name='email_registration_confirm'),
)
