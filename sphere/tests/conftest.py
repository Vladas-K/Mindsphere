"""Shared test data; all database records and uploads are isolated per test."""
from pathlib import Path
from types import SimpleNamespace

from django.contrib.admin import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from events.admin import EventAdmin
from events.models import Category, Event


@pytest.fixture(autouse=True)
def isolated_test_settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / 'media'
    settings.MEDIA_URL = '/media/'
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']


@pytest.fixture
def category(db):
    return Category.objects.create(name='Программы', slug='programs')


@pytest.fixture
def employee(db, django_user_model):
    return django_user_model.objects.create_user(
        username='employee', password='Employee-test-password', first_name='Анна',
    )


@pytest.fixture
def superuser(db, django_user_model):
    return django_user_model.objects.create_superuser(username='owner')


@pytest.fixture
def authenticated_client(client, employee):
    client.force_login(employee)
    return client


@pytest.fixture
def catalog_event(category):
    return Event.objects.create(
        name='Бурлеск', slug='burlesque', category=category,
        short_description='Публичное описание программы.',
        description='ВНУТРЕННИЙ СЦЕНАРИЙ, ТОЛЬКО ДЛЯ КОМАНДЫ',
        slogan='Шоу, которое не скроет эмоций', scenario='Музыкальный спектакль',
        program_format='Музыкальный вечер', sort_order=2,
    )


@pytest.fixture
def image_upload():
    return SimpleUploadedFile(
        'small.gif',
        b'GIF89a\x02\x00\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xff\xff\xff!\xf9\x04\x00\x00\x00\x00\x00,\x00'
        b'\x00\x00\x00\x02\x00\x01\x00\x00\x02\x02\x0c\x0a\x00;',
        content_type='image/gif',
    )


@pytest.fixture
def form_data(category, image_upload):
    return {
        'name': 'Тестовое название', 'slug': 'test-slug-form',
        'description': 'Тестовая запись через форму',
        'category': category.pk, 'image': image_upload,
    }


@pytest.fixture
def ordering(db):
    # Deliberately include tied priorities, zero and a hidden record.
    return SimpleNamespace(
        a=Event.objects.create(name='A', slug='a', sort_order=0),
        b=Event.objects.create(name='B', slug='b', sort_order=1),
        c=Event.objects.create(name='C', slug='c', sort_order=1),
        hidden=Event.objects.create(name='Hidden', slug='hidden', sort_order=0, is_published=False),
    )


@pytest.fixture
def model_admin():
    return EventAdmin(Event, AdminSite())


@pytest.fixture
def env_file(tmp_path):
    return tmp_path / '.env'


@pytest.fixture
def sphere_root():
    return Path(__file__).resolve().parents[1]
