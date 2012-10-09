#!/usr/bin/env python

from distutils.core import setup
import os
import setuplib

packages, package_data = setuplib.find_packages('email_registration')

setup(name='django-email-registration',
    version=__import__('email_registration').__version__,
    description='So simple you\'ll burst into tears right away.',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    author='Matthias Kestenholz',
    author_email='mk@406.ch',
    url='http://github.com/matthiask/django-email-registration/',
    license='BSD License',
    platforms=['OS Independent'],
    packages=packages,
    package_data=package_data,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
)
