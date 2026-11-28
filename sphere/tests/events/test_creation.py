from http import HTTPStatus

from django.urls import reverse
from pytest_django.asserts import assertRedirects
import pytest

from events.models import Event


pytestmark = pytest.mark.django_db


def test_create_event(authenticated_client, category, form_data):
    """Preserve both the form fields and the bytes of an uploaded image."""
    response = authenticated_client.post(reverse('events:event_create'), data=form_data)
    assertRedirects(response, reverse('events:index'))
    assert response.status_code == HTTPStatus.FOUND
    assert Event.objects.count() == 1
    event = Event.objects.get()
    assert event.name == form_data['name']
    assert event.slug == form_data['slug']
    assert event.description == form_data['description']
    assert event.category == category
    assert event.image.name == 'events/small.gif'
    with event.image.open('rb') as image:
        form_data['image'].seek(0)
        assert image.read() == form_data['image'].read()


def test_anonymous_user_cant_create_event(client, form_data):
    client.post(reverse('events:event_create'), data=form_data)
    assert not Event.objects.exists()
