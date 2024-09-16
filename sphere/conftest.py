import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from events.models import Event, Category


@pytest.fixture
def category():
    category = Category.objects.create(
        name='example category', 
        slug='example-slug'
    )
    return category


@pytest.fixture
def event(category):
    event = Event.objects.create(
        name='example event', 
        description = 'example-description', 
        slug='example-slug',
        category=category
    )
    return event


@pytest.fixture
def user(django_user_model):
    user = django_user_model.objects.create(username='HasNoName')
    return user


@pytest.fixture
def form_data(category):
    small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
    uploaded = SimpleUploadedFile(
        name='small.gif',
        content=small_gif,
        content_type='image/gif'
    )

    form_data = {
            'name': 'Тестовое название',
            'slug': 'Test-slug-form',
            'description': 'Тестовая запись через форму',
            'category': category.pk,
            'image': uploaded,
        }
    return form_data