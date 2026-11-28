from unittest.mock import patch
import json
import os
import subprocess
import sys

from django.core.exceptions import ImproperlyConfigured
import pytest

from config.environment import env_bool, load_env


def test_values_quotes_and_existing_environment(env_file):
    env_file.write_text('# comment\n\nDJANGO_SECRET_KEY="file-secret=#literal"\nDJANGO_ALLOWED_HOSTS=\'example.com, www.example.com\'\nEMPTY=\n')
    with patch.dict(os.environ, {'DJANGO_SECRET_KEY': 'server-secret'}, clear=True):
        load_env(env_file)
        assert os.environ['DJANGO_SECRET_KEY'] == 'server-secret'
        assert os.environ['DJANGO_ALLOWED_HOSTS'] == 'example.com, www.example.com'
        assert os.environ['EMPTY'] == ''


def test_missing_file_does_not_require_dotenv(env_file):
    with patch.dict(os.environ, {}, clear=True):
        load_env(env_file)
        assert dict(os.environ) == {}


def test_values_are_not_executed_or_expanded(env_file):
    value = '$(echo secret)-${HOME}-`echo secret`'
    env_file.write_text('DJANGO_SECRET_KEY=' + value)
    with patch.dict(os.environ, {}, clear=True):
        load_env(env_file)
        assert os.environ['DJANGO_SECRET_KEY'] == value


@pytest.mark.parametrize('line', [
    'not-an-assignment', 'BAD-KEY=private-value', 'KEY="private-value',
])
def test_invalid_entries_fail_without_disclosing_values(env_file, line):
    env_file.write_text(line)
    with pytest.raises(ImproperlyConfigured) as error:
        load_env(env_file)
    assert 'private-value' not in str(error.value)


def test_boolean_values_and_misspellings():
    for value, expected in [('true', True), ('0', False), (' YES ', True)]:
        with patch.dict(os.environ, {'FLAG': value}):
            assert env_bool('FLAG') == expected
    with patch.dict(os.environ, {'FLAG': 'tru'}):
        with pytest.raises(ImproperlyConfigured):
            env_bool('FLAG')


def inspect_settings(env_file, sphere_root, module='config.production', overrides=None):
    env = {key: value for key, value in os.environ.items() if not key.startswith('DJANGO_')}
    env.update({'PYTHONPATH': str(sphere_root), 'DJANGO_ENV_FILE': str(env_file)})
    env.update(overrides or {})
    # A fresh interpreter keeps production settings separate from pytest settings.
    script = f"""
import importlib
import json

s = importlib.import_module({module!r})
print(json.dumps({{
    'debug': s.DEBUG,
    'hosts': s.ALLOWED_HOSTS,
    'static_root': str(getattr(s, 'STATIC_ROOT', None)),
    'database': str(s.DATABASES['default']['NAME']),
    'media': str(s.MEDIA_ROOT),
    'session_secure': getattr(s, 'SESSION_COOKIE_SECURE', False),
    'csrf_secure': getattr(s, 'CSRF_COOKIE_SECURE', False),
    'redirect': getattr(s, 'SECURE_SSL_REDIRECT', False),
    'secret_from_file': s.SECRET_KEY == 'test-production-secret',
}}))
"""
    return subprocess.run(
        [sys.executable, '-c', script], env=env,
        capture_output=True, text=True, check=False,
    )


def test_production_loads_file_and_keeps_existing_data_paths(env_file, sphere_root):
    env_file.write_text('DJANGO_SECRET_KEY=test-production-secret\nDJANGO_ALLOWED_HOSTS=example.com, test.example.com\n')
    result = inspect_settings(env_file, sphere_root)
    assert result.returncode == 0, result.stderr
    values = json.loads(result.stdout)
    assert not values['debug']
    assert values['hosts'] == ['example.com', 'test.example.com']
    assert values['secret_from_file']
    assert values['session_secure']
    assert values['csrf_secure']
    assert not values['redirect']
    assert values['static_root'] == str(sphere_root.parent / 'public_html/static')
    assert values['database'] == str(sphere_root / 'db.sqlite3')
    assert values['media'] == str(sphere_root / 'media')


def test_production_does_not_fall_back_to_development_secret(env_file, sphere_root):
    result = inspect_settings(env_file, sphere_root, overrides={'DJANGO_ALLOWED_HOSTS': 'example.com'})
    assert result.returncode != 0
    assert 'DJANGO_SECRET_KEY is required' in result.stderr


def test_production_requires_hosts(env_file, sphere_root):
    result = inspect_settings(env_file, sphere_root, overrides={'DJANGO_SECRET_KEY': 'test-production-secret'})
    assert result.returncode != 0
    assert 'DJANGO_ALLOWED_HOSTS is required' in result.stderr


def test_process_environment_overrides_file_and_enables_redirect(env_file, sphere_root):
    env_file.write_text('DJANGO_SECRET_KEY=file-value\nDJANGO_ALLOWED_HOSTS=file.example\n')
    result = inspect_settings(env_file, sphere_root, overrides={'DJANGO_SECRET_KEY': 'test-production-secret', 'DJANGO_ALLOWED_HOSTS': 'server.example', 'DJANGO_SECURE_SSL_REDIRECT': 'true'})
    assert result.returncode == 0, result.stderr
    values = json.loads(result.stdout)
    assert values['secret_from_file']
    assert values['hosts'] == ['server.example']
    assert values['redirect']


def test_local_settings_do_not_load_server_file(env_file, sphere_root):
    env_file.write_text('DJANGO_SECRET_KEY=test-production-secret\n')
    result = inspect_settings(env_file, sphere_root, module='config.settings')
    assert result.returncode == 0, result.stderr
    values = json.loads(result.stdout)
    assert values['debug']
    assert '127.0.0.1' in values['hosts']
    assert not values['secret_from_file']
