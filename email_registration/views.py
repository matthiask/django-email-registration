from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.db.models.fields import FieldDoesNotExist
from django.shortcuts import redirect, render
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.decorators.http import require_POST

from email_registration.signals import password_set
from email_registration.utils import (
    InvalidCode, decode, send_registration_mail)

User = get_user_model()
USERNAME_FIELD = User.USERNAME_FIELD


class RegistrationForm(forms.Form):
    email = forms.EmailField(
        label=ugettext_lazy('email address'),
        max_length=75,
        widget=forms.TextInput(attrs={
            'placeholder': ugettext_lazy('email address'),
        }),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(_(
                'This email address already exists as an account.'
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


def email_registration_confirm(request, code, max_age=3 * 86400,
                               form_class=SetPasswordForm):
    try:
        email, user = decode(code, max_age=max_age)
    except InvalidCode as exc:
        messages.error(request, '%s' % exc)
        return redirect('/')

    if not user:
        if User.objects.filter(email=email).exists():
            messages.error(request, _(
                'This email address already exists as an account.'
                ' Did you want to reset your password?'))
            return redirect('/')

        username_field = User._meta.get_field(USERNAME_FIELD)

        kwargs = {}
        if username_field.name == 'email':
            kwargs['email'] = email
        else:
            username = email

            # If email exceeds max length of field set username to random
            # string
            max_length = username_field.max_length
            if len(username) > max_length:
                username = get_random_string(
                    25 if max_length >= 25 else max_length)
            kwargs[username_field.name] = username

            # Set value for 'email' field in case the user model has one
            try:
                User._meta.get_field('email')
                kwargs['email'] = email
            except FieldDoesNotExist:
                pass

        user = User(**kwargs)

    if request.method == 'POST':
        form = form_class(user, request.POST)
        if form.is_valid():
            user = form.save()

            password_set.send(
                sender=user.__class__,
                request=request,
                user=user,
                password=form.cleaned_data.get('new_password1'),
            )

            messages.success(request, _(
                'Successfully set the new password. Please login now.'))

            return redirect('login')

    else:
        messages.success(request, _('Please set a password.'))
        form = form_class(user)

    return render(request, 'registration/password_set_form.html', {
        'form': form,
    })
