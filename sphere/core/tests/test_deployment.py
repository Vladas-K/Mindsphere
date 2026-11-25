import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.environment import env_bool, load_env


class EnvironmentFileTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / '.env'

    def test_values_quotes_and_existing_environment(self):
        self.path.write_text(
            '# comment\n\nDJANGO_SECRET_KEY="file-secret=#literal"\n'
            "DJANGO_ALLOWED_HOSTS='example.com, www.example.com'\n"
            'EMPTY=\n',
        )
        with patch.dict(os.environ, {'DJANGO_SECRET_KEY': 'server-secret'}, clear=True):
            load_env(self.path)
            self.assertEqual(os.environ['DJANGO_SECRET_KEY'], 'server-secret')
            self.assertEqual(os.environ['DJANGO_ALLOWED_HOSTS'], 'example.com, www.example.com')
            self.assertEqual(os.environ['EMPTY'], '')

    def test_missing_file_does_not_require_dotenv(self):
        with patch.dict(os.environ, {}, clear=True):
            load_env(self.path)
            self.assertEqual(dict(os.environ), {})

    def test_values_are_not_executed_or_expanded(self):
        value = '$(echo secret)-${HOME}-`echo secret`'
        self.path.write_text('DJANGO_SECRET_KEY=' + value)
        with patch.dict(os.environ, {}, clear=True):
            load_env(self.path)
            self.assertEqual(os.environ['DJANGO_SECRET_KEY'], value)

    def test_invalid_entries_fail_without_disclosing_values(self):
        for line in ('not-an-assignment', 'BAD-KEY=private-value', 'KEY="private-value'):
            with self.subTest(line=line):
                self.path.write_text(line)
                with self.assertRaises(ImproperlyConfigured) as error:
                    load_env(self.path)
                self.assertNotIn('private-value', str(error.exception))

    def test_boolean_values_and_misspellings(self):
        for value, expected in [('true', True), ('0', False), (' YES ', True)]:
            with self.subTest(value=value), patch.dict(os.environ, {'FLAG': value}):
                self.assertEqual(env_bool('FLAG'), expected)
        with patch.dict(os.environ, {'FLAG': 'tru'}):
            with self.assertRaises(ImproperlyConfigured):
                env_bool('FLAG')


class ProductionSettingsTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env_file = Path(self.temp.name) / '.env'
        self.sphere = Path(__file__).resolve().parents[2]

    def inspect_settings(self, module='config.production', overrides=None):
        env = {
            key: value for key, value in os.environ.items()
            if not key.startswith('DJANGO_')
        }
        env.update({
            'PYTHONPATH': str(self.sphere),
            'DJANGO_ENV_FILE': str(self.env_file),
        })
        env.update(overrides or {})
        # A fresh interpreter avoids mixing production and test settings.
        return subprocess.run(
            [sys.executable, '-c', f"""
import importlib, json
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
"""], env=env, capture_output=True, text=True, check=False,
        )

    def test_production_loads_file_and_keeps_existing_data_paths(self):
        self.env_file.write_text(
            'DJANGO_SECRET_KEY=test-production-secret\n'
            'DJANGO_ALLOWED_HOSTS=example.com, test.example.com\n'
        )
        result = self.inspect_settings()
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertFalse(values['debug'])
        self.assertEqual(values['hosts'], ['example.com', 'test.example.com'])
        self.assertTrue(values['secret_from_file'])
        self.assertTrue(values['session_secure'])
        self.assertTrue(values['csrf_secure'])
        self.assertFalse(values['redirect'])
        self.assertEqual(values['static_root'], str(self.sphere.parent / 'public_html/static'))
        self.assertEqual(values['database'], str(self.sphere / 'db.sqlite3'))
        self.assertEqual(values['media'], str(self.sphere / 'media'))

    def test_production_does_not_fall_back_to_development_secret(self):
        result = self.inspect_settings(overrides={'DJANGO_ALLOWED_HOSTS': 'example.com'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DJANGO_SECRET_KEY is required', result.stderr)

    def test_production_requires_hosts(self):
        result = self.inspect_settings(overrides={'DJANGO_SECRET_KEY': 'test-production-secret'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DJANGO_ALLOWED_HOSTS is required', result.stderr)

    def test_process_environment_overrides_file_and_enables_redirect(self):
        self.env_file.write_text('DJANGO_SECRET_KEY=file-value\nDJANGO_ALLOWED_HOSTS=file.example\n')
        result = self.inspect_settings(overrides={
            'DJANGO_SECRET_KEY': 'test-production-secret',
            'DJANGO_ALLOWED_HOSTS': 'server.example',
            'DJANGO_SECURE_SSL_REDIRECT': 'true',
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertTrue(values['secret_from_file'])
        self.assertEqual(values['hosts'], ['server.example'])
        self.assertTrue(values['redirect'])

    def test_local_settings_do_not_load_server_file(self):
        self.env_file.write_text('DJANGO_SECRET_KEY=test-production-secret\n')
        result = self.inspect_settings(module='config.settings')
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertTrue(values['debug'])
        self.assertIn('127.0.0.1', values['hosts'])
        self.assertFalse(values['secret_from_file'])
