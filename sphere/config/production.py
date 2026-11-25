"""Server settings shared by Passenger and management commands."""

import os

from django.core.exceptions import ImproperlyConfigured

from .environment import env_bool, load_env
from .settings import *  # noqa: F403
from .settings import BASE_DIR


load_env(os.environ.get('DJANGO_ENV_FILE', BASE_DIR.parent / '.env'))

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '').strip()
if not SECRET_KEY:
    raise ImproperlyConfigured('DJANGO_SECRET_KEY is required for production.')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
    if host.strip()
]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured('DJANGO_ALLOWED_HOSTS is required for production.')

DEBUG = False
STATIC_ROOT = BASE_DIR.parent / 'public_html' / 'static'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Keep the HTTP test catalog available until HTTPS is ready. No proxy header is
# trusted implicitly; check the actual Beget HTTPS setup before enabling this.
SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT')
