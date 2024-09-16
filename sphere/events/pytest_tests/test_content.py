import pytest
from django.urls import reverse
from events.models import Event


@pytest.mark.django_db
def test_event_in_list(event, client):
    url = reverse('events:index')
    response = client.get(url)
    object_list = response.context['object_list']
    assert event in object_list


def test_create_event_page_contains_form(client, user):
    url = reverse('events:event_create')
    client.force_login(user)
    response = client.get(url)
    assert 'form' in response.context


@pytest.mark.django_db
def test_anonymous_user_cant_create_event(client, form_data):
    url = reverse('events:event_create')
    client.post(url, data=form_data)
    assert Event.objects.count() == 0 
