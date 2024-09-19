import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects
from events.models import Event


@pytest.mark.django_db
def test_anonymous_user_cant_create_event(client, form_data):
    url = reverse('events:event_create')
    client.post(url, data=form_data)
    assert Event.objects.count() == 0

def test_auth_user_can_create_event(client, user, form_data):
    url = reverse('events:event_create')
    client.force_login(user)
    response = client.post(url, data=form_data)
    assertRedirects(response, reverse('events:index'))
    assert Event.objects.count() == 1
    new_event = Event.objects.get()
    assert new_event.name == form_data['name']
    assert new_event.slug == form_data['slug']
    assert new_event.description == form_data['description']
    assert new_event.category.pk == form_data['category']
    with new_event.image.open('rb') as new_image_file:
        form_data['image'].seek(0)
        assert new_image_file.read() == form_data['image'].read()
