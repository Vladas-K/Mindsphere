from django.contrib import admin
from django.test import RequestFactory
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains
import pytest

from events.forms import EventForm
from events.models import Event

pytestmark = pytest.mark.django_db


def test_employee_cannot_change_slogan_through_create_or_edit(catalog_event, client, employee):
    previous_slogan = catalog_event.slogan
    client.force_login(employee)
    create_url = reverse('events:event_create')
    edit_url = reverse('events:event_edit', args=[catalog_event.slug])
    for url in (create_url, edit_url):
        assertNotContains(client.get(url), 'id="id_slogan"')
        assertContains(client.get(url), 'со встроенным слоганом')
    response = client.post(create_url, {'name': 'Новая', 'slug': 'new', 'slogan': 'Подставленный слоган'})
    assert response.status_code == 302
    assert Event.objects.get(slug='new').slogan == ''
    response = client.post(edit_url, {'name': 'Изменённое название', 'slug': catalog_event.slug, 'slogan': 'Подмена'})
    assert response.status_code == 302
    catalog_event.refresh_from_db()
    assert catalog_event.slogan == previous_slogan
    assert catalog_event.name == 'Изменённое название'


def test_superuser_can_create_edit_and_clear_slogan(catalog_event, client, superuser):
    client.force_login(superuser)
    create_url = reverse('events:event_create')
    assertContains(client.get(create_url), 'id="id_slogan"')
    assertContains(client.get(create_url), 'только суперпользователю')
    client.post(create_url, {'name': 'Новая', 'slug': 'new', 'slogan': 'Новый слоган'})
    assert Event.objects.get(slug='new').slogan == 'Новый слоган'
    edit_url = reverse('events:event_edit', args=[catalog_event.slug])
    assertContains(client.get(edit_url), 'id="id_slogan"')
    for slogan in ('Изменённый слоган', ''):
        response = client.post(edit_url, {'name': catalog_event.name, 'slug': catalog_event.slug, 'slogan': slogan})
        assert response.status_code == 302
        catalog_event.refresh_from_db()
        assert catalog_event.slogan == slogan


def test_admin_uses_same_superuser_restriction(employee, superuser):
    model_admin = admin.site._registry[Event]
    for user, allowed in ((employee, False), (superuser, True)):
        request = RequestFactory().get('/admin/events/event/add/')
        request.user = user
        form = model_admin.get_form(request)()
        assert ('slogan' in form.fields) == allowed
        names = [name for _, options in model_admin.get_fieldsets(request) for name in options['fields']]
        assert ('slogan' in names) == allowed
    employee.is_staff = True
    assert 'slogan' not in EventForm(user=employee).fields
    assert 'slogan' not in EventForm().fields
