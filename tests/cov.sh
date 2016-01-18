#!/bin/sh
venv/bin/coverage run --branch --include="*email_registration/*" --omit="*tests*" ./manage.py test testapp
venv/bin/coverage html
