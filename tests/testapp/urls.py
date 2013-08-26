from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse


admin.autodiscover()


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', lambda request: HttpResponse(repr(request.REQUEST))),
    url(r'^ac/', include('django.contrib.auth.urls')),
    url(r'^er/', include('email_registration.urls')),
) + staticfiles_urlpatterns()
