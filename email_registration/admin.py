from django.contrib import admin

from . import models


admin.site.register(models.Registration,
    list_display=('code', 'email', 'sent_on'),
    search_fields=('code', 'email'),
    )
