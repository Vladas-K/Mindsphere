import pytest
from django.urls import reverse
from http import HTTPStatus


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, kwargs',
    [
        ('events:index', None),
        ('events:about', None),
        ('users:login', None),
        ('users:logout', None),
        ('events:event_detail', {'slug': 'example-slug'}),
        ('events:category_events', {'cat_slug': 'example-slug'})
    ]
)
def test_pages_availability_for_anonymous_user(client, name, kwargs, event, category):
    url = reverse(name, kwargs=kwargs)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name',
     ['events:event_create']
)
def test_pages_availability_for_auth_user(client, user, name):
    url = reverse(name)
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, kwargs',
    [
        ('events:event_create', None),
        ('events:event_delete', {'slug': 'example-slug'}),
        ('events:event_edit', {'slug': 'example-slug'}),
    ]
)
def test_redirects(client, name, kwargs, event, category):
    url = reverse(name, kwargs=kwargs)
    response = client.get(url)
    assert response.status_code == HTTPStatus.FOUND
