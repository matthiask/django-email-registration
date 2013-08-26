from django import forms
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.decorators.http import require_POST

from email_registration.signals import password_set
from email_registration.utils import (InvalidCode, decode,
    send_registration_mail)


class RegistrationForm(forms.Form):
    email = forms.EmailField(label=ugettext_lazy('email address'),
        widget=forms.TextInput(attrs={
            'placeholder': ugettext_lazy('email address'),
            }), max_length=75)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _('This email address already exists as an account.'
                    ' Did you want to reset your password?'))
        return email


@require_POST
def email_registration_form(request, form_class=RegistrationForm):
    # TODO unajaxify this view for the release?
    form = form_class(request.POST)

    if form.is_valid():
        email = form.cleaned_data['email']
        send_registration_mail(email, request)

        return render(request, 'registration/email_registration_sent.html', {
            'email': email,
            })

    return render(request, 'registration/email_registration_form.html', {
        'form': form,
        })


def email_registration_confirm(request, code, max_age=3 * 86400):
    try:
        email, user = decode(code, max_age=max_age)
    except InvalidCode as exc:
        messages.error(request, exc[0])
        return redirect('/')

    if not user:
        if User.objects.filter(email=email).exists():
            messages.error(request,
                _('This email address already exists as an account.'
                    ' Did you want to reset your password?'))
            return redirect('/')

        user = User(
            username=email if len(email) <= 30 else get_random_string(25),
            email=email)

    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            user = form.save()

            password_set.send(
                sender=user.__class__,
                request=request,
                user=user,
                password=form.cleaned_data.get('new_password1'),
                )

            messages.success(request,
                _('Successfully set the new password. Please login now.'))

            return redirect('login')

    else:
        messages.success(request, _('Please set a password.'))
        form = SetPasswordForm(user)

    return render(request, 'registration/password_set_form.html', {
        'form': form,
        })
