from django.urls import path

from email_registration.views import email_registration_confirm, email_registration_form


urlpatterns = [
    path(
        "",
        email_registration_form,
        name="email_registration_form",
    ),
    path(
        "<str:code>/",
        email_registration_confirm,
        name="email_registration_confirm",
    ),
]
