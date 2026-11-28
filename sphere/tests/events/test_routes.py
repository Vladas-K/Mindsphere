from http import HTTPStatus

from django.urls import reverse
from pytest_django.asserts import assertRedirects
import pytest


pytestmark = pytest.mark.django_db


def test_create(authenticated_client):
    response = authenticated_client.get(reverse('events:event_create'))
    assert response.status_code == HTTPStatus.OK
    assert 'form' in response.context


@pytest.mark.parametrize('name,method', [
    ('events:index', 'get'), ('users:login', 'get'),
    ('users:logout', 'post'), ('events:category_events', 'get'),
])
def test_pages_availability(client, category, name, method):
    args = [category.slug] if name == 'events:category_events' else None
    response = getattr(client, method)(reverse(name, args=args))
    assert response.status_code == HTTPStatus.OK


def test_logout_uses_post(authenticated_client):
    assert authenticated_client.get(reverse('users:logout')).status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert authenticated_client.post(reverse('users:logout')).status_code == HTTPStatus.OK


def test_detail_requires_login(client, employee, catalog_event):
    url = catalog_event.get_absolute_url()
    assertRedirects(client.get(url), reverse('users:login') + '?next=' + url)
    client.force_login(employee)
    assert client.get(url).status_code == HTTPStatus.OK


@pytest.mark.parametrize('name', ['event_detail', 'event_create', 'event_delete', 'event_edit'])
@pytest.mark.parametrize('method', ['get', 'post'])
def test_redirects(client, catalog_event, name, method):
    args = None if name == 'event_create' else [catalog_event.slug]
    url = reverse('events:' + name, args=args)
    assertRedirects(getattr(client, method)(url), reverse('users:login') + '?next=' + url)
