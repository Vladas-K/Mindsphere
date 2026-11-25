"""Read the small KEY=value file used by the Beget deployment."""

import os
import re
import shlex
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def load_env(path):
    """Load .env without overriding variables supplied by the server.

    Supports blank lines, full-line comments and optionally quoted values.
    Shell commands and variable substitutions are never evaluated.
    """
    path = Path(path)
    if not path.exists():
        return

    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, separator, value = line.partition('=')
        name, value = name.strip(), value.strip()
        if not separator or not re.fullmatch(r'[A-Z_][A-Z0-9_]*', name):
            raise ImproperlyConfigured(f'Invalid .env entry at line {number}.')
        if value.startswith(('"', "'")):
            try:
                parts = shlex.split(value)
            except ValueError:
                raise ImproperlyConfigured(
                    f'Invalid .env quoting at line {number}.'
                ) from None
            if len(parts) != 1:
                raise ImproperlyConfigured(f'Invalid .env value at line {number}.')
            value = parts[0]
        os.environ.setdefault(name, value)


def env_bool(name, default=False):
    value = os.environ.get(name, str(default)).strip().lower()
    if value in ('1', 'true', 'yes', 'on'):
        return True
    if value in ('0', 'false', 'no', 'off'):
        return False
    raise ImproperlyConfigured(f'{name} must be true or false.')
