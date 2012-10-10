from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.decorators.http import require_POST

from email_registration.models import Registration, generate_code


class RegistrationForm(forms.Form):
    email = forms.EmailField(label=ugettext_lazy('e-mail address'),
        widget=forms.TextInput(attrs={
            'placeholder': ugettext_lazy('e-mail address'),
            }))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email):
            raise forms.ValidationError(
_('This e-mail address already exists as an account. Do you want to reset your password?'))
        return email


@require_POST
def email_registration_form(request):
    form = RegistrationForm(request.POST)

    if form.is_valid():
        email = form.cleaned_data['email']
        try:
            registration = Registration.objects.get(email=email)
        except Registration.DoesNotExist:
            registration = Registration(email=email)

        registration.send_mail()

        return render(request, 'registration/email_registration_sent.html', {
            'email': email,
            })

    return render(request, 'registration/email_registration_form.html', {
        'form': form,
        })


def email_registration_confirm(request, code):
    code = get_object_or_404(Registration, code=code)

    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()

            messages.success(request,
                _('Successfully set the new password.'))

            code.delete()

            return redirect('/')

    else:
        # We need a known password for the authentication step below
        temporary = generate_code(20)

        if not code.user:
            code.user = User.objects.create_user(code.email, email=code.email,
                password=temporary)

            messages.success(request,
                _('Successfully created a new user. Please set a password.'))

        else:
            code.user.set_password(temporary)
            code.user.save()

            messages.success(request, _('Please set a password.'))

        user = authenticate(username=code.user.username, password=temporary)
        login(request, user)

        code.save()

        form = SetPasswordForm(request.user)

    return render(request, 'registration/password_set_form.html', {
        'form': form,
        })
