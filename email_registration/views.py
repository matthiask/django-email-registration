from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.core.signing import BadSignature, SignatureExpired
from django.shortcuts import redirect, render
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.decorators.http import require_POST

from email_registration.utils import get_signer, send_registration_mail


class RegistrationForm(forms.Form):
    email = forms.EmailField(label=ugettext_lazy('e-mail address'),
        widget=forms.TextInput(attrs={
            'placeholder': ugettext_lazy('e-mail address'),
            }))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email):
            raise forms.ValidationError(
                _('This e-mail address already exists as an account.'
                    ' Do you want to reset your password?'))
        return email


@require_POST
def email_registration_form(request):
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
        data = get_signer().unsign(code, max_age=1800)
    except SignatureExpired:
        messages.error(request, _('The link is expired. Please request another'
            ' registration link.'))
        return redirect('/')

    except BadSignature:
        messages.error(request, _('Unable to verify the signature. Please'
            ' request a new registration link.'))
        return redirect('/')

    parts = data.rsplit('-', 1)
    email = parts[0]
    if len(parts) == 2 and parts[1]:
        try:
            user = User.objects.get(pk=parts[1])
        except (User.DoesNotExist, TypeError, ValueError):
            messages.error(request, _('Something went wrong while decoding the'
                ' registration request. Please try again.'))
            return redirect('/')
    else:
        user = None

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

        if not user:
            user = User.objects.create_user(email, email=email,
                password=temporary)

            messages.success(request,
                _('Successfully created a new user. Please set a password.'))

        else:
            user.set_password(temporary)
            user.save()

            messages.success(request, _('Please set a password.'))

        user = authenticate(username=user.username, password=temporary)
        login(request, user)

        form = SetPasswordForm(request.user)

    return render(request, 'registration/password_set_form.html', {
        'form': form,
        })
