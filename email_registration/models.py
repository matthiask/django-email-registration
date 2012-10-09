import random
import string

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


def generate_code(length):
    return u''.join(random.choice(string.ascii_letters + string.digits)
        for i in range(length))


class Registration(models.Model):
    sent_on = models.DateTimeField(_('sent on'), default=timezone.now)
    code = models.CharField(_('code'), max_length=40, unique=True)
    email = models.EmailField(_('e-mail address'), unique=True)
    user = models.ForeignKey(User, verbose_name=_('user'),
        blank=True, null=True)

    class Meta:
        verbose_name = _('registration')
        verbose_name_plural = _('registrations')

    def __unicode__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_code(40)
        super(Registration, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('email_registration_confirm', (), {'code': self.code})
