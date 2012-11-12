from django.dispatch import Signal


password_set = Signal(providing_args=['request', 'user', 'password'])
