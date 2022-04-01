from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views import generic

from email_registration.views import email_registration_confirm


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", generic.TemplateView.as_view(template_name="base.html")),
    path("ac/", include("django.contrib.auth.urls")),
    path("er/", include("email_registration.urls")),
    path("er-quick/<str:code>/", email_registration_confirm, {"max_age": 1}),
] + staticfiles_urlpatterns()
