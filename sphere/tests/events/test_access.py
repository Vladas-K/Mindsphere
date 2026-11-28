from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects
import pytest

from events.models import Event

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('catalog_event', 'employee')]


def test_public_catalog_does_not_expose_internal_content_or_links(catalog_event, category, client):
    for url in (reverse('events:index'), category.get_absolute_url()):
        response = client.get(url)
        assertContains(response, catalog_event.short_description)
        assertContains(response, catalog_event.slogan)
        assertContains(response, catalog_event.scenario)
        assertContains(response, catalog_event.program_format)
        assertContains(response, '#program-' + str(catalog_event.pk))
        assertNotContains(response, catalog_event.description)
        assertNotContains(response, 'Подробнее')
        assertNotContains(response, catalog_event.get_absolute_url())
        assertNotContains(response, 'Интерактивы')


def test_empty_summary_does_not_fall_back_to_private_description(catalog_event, client):
    Event.objects.filter(pk=catalog_event.pk).update(short_description='')
    response = client.get(reverse('events:index'))
    assertNotContains(response, catalog_event.description)


def test_empty_internal_description_offers_edit_link(catalog_event, client, employee):
    client.force_login(employee)
    for text in ('', ' \n '):
        Event.objects.filter(pk=catalog_event.pk).update(description=text)
        response = client.get(catalog_event.get_absolute_url())
        assertContains(response, 'Полное описание пока не добавлено.')
        assertContains(response, 'Добавить описание')
        assertContains(response, reverse('events:event_edit', args=[catalog_event.slug]) + '#id_description')
        assertContains(response, reverse('events:event_delete', args=[catalog_event.slug]))
        assertNotContains(response, 'cdn.jsdelivr.net')


def test_internal_description_preserves_line_breaks_and_escapes_html(catalog_event, client, employee):
    client.force_login(employee)
    Event.objects.filter(pk=catalog_event.pk).update(description='Первая строка\n<script>private()</script>')
    response = client.get(catalog_event.get_absolute_url())
    assertContains(response, 'Первая строка<br>&lt;script&gt;private()&lt;/script&gt;')
    assertNotContains(response, '<script>private()')
    assertContains(response, 'Редактировать описание')
    assertNotContains(response, 'Полное описание пока не добавлено.')


def test_public_page_has_no_staff_navigation_or_filters(client):
    response = client.get(reverse('events:index'))
    assertNotContains(response, 'Вход для сотрудников')
    assertNotContains(response, reverse('users:login'))
    assertNotContains(response, 'staff-bar')
    assertNotContains(response, 'Категории программ')
    assertNotContains(response, 'site-header')
    assertContains(response, '<h2>Бурлеск</h2>')


def test_guests_cannot_open_or_modify_internal_cards(catalog_event, client):
    for name in ('event_detail', 'event_edit', 'event_delete'):
        url = reverse('events:' + name, args=[catalog_event.slug])
        for method in ('get', 'post'):
            response = getattr(client, method)(url)
            assertRedirects(response, reverse('users:login') + '?next=' + url)
    assert Event.objects.filter(pk=catalog_event.pk).exists()
