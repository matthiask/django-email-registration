from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views import generic

from email_registration.views import email_registration_confirm


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', generic.TemplateView.as_view(template_name='base.html')),
    url(r'^ac/', include('django.contrib.auth.urls')),
    url(r'^er/', include('email_registration.urls')),

    url(r'^er-quick/(?P<code>[^/]+)/$',
        email_registration_confirm,
        {'max_age': 1}),

] + staticfiles_urlpatterns()
