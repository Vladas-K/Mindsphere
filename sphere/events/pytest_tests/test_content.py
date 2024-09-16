import pytest
from django.urls import reverse


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
