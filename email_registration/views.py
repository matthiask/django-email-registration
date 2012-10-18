from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.decorators.http import require_POST

from email_registration.utils import (InvalidCode, decode,
    send_registration_mail)


class RegistrationForm(forms.Form):
    email = forms.EmailField(label=ugettext_lazy('e-mail address'),
        widget=forms.TextInput(attrs={
            'placeholder': ugettext_lazy('e-mail address'),
            }))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _('This e-mail address already exists as an account.'
                    ' Do you want to reset your password?'))
        return email


@require_POST
def email_registration_form(request):
    # TODO unajaxify this view for the release?
    form = RegistrationForm(request.POST)

    if form.is_valid():
        email = form.cleaned_data['email']
        send_registration_mail(email, request)

        return render(request, 'registration/email_registration_sent.html', {
            'email': email,
            })

    return render(request, 'registration/email_registration_form.html', {
        'form': form,
        })


def email_registration_confirm(request, code):
    try:
        email, user = decode(code)
    except InvalidCode as exc:
        messages.error(request, exc[0])
        return redirect('/')

    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()

            messages.success(request,
                _('Successfully set the new password.'))

            return redirect('/')

    else:
        # We need a known password for the authentication step below
        temporary = get_random_string()

        if user:
            user.set_password(temporary)
            user.save()
            messages.success(request, _('Please set a password.'))

        else:
            try:
                # When the user visits this page more than once, the user
                # instance already exists in the database
                user = User.objects.get(username=email)
                user.set_password(temporary)
                user.save()
            except User.DoesNotExist:
                user = User.objects.create_user(email, email=email,
                    password=temporary)

            messages.success(request,
                _('Successfully created a new user. Please set a password.'))

        user = authenticate(username=user.username, password=temporary)
        login(request, user)

        form = SetPasswordForm(request.user)

    return render(request, 'registration/password_set_form.html', {
        'form': form,
        })
