from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains
import pytest

from events.catalog import catalog_source
from events.models import Event

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('catalog_event', 'employee')]


def test_complete_catalog_import_is_repeatable(catalog_event, client):
    for _ in range(2):
        call_command('load_catalog', replace=True, stdout=StringIO())
    active = Event.objects.filter(is_published=True)
    expected = catalog_source()['programs']
    assert active.count() == 21
    assert list(active.values_list('name', flat=True)) == [r['name'] for r in expected]
    assert Event.objects.get(pk=catalog_event.pk).description == catalog_event.description
    assert get_user_model().objects.count() == 1
    for event, row in zip(active, expected):
        assert event.catalog_page == row['catalog_page']
        assert event.short_description == row['short_description']
        assert Path(event.image.path).is_file()
    old = Event.objects.create(name='Старая программа', description='private')
    call_command('load_catalog', replace=True, stdout=StringIO())
    old.refresh_from_db()
    assert not old.is_published
    response = client.get(reverse('events:index'))
    assertContains(response, 'class="catalog-page program-sheet"', count=21)
    assertContains(response, 'class="catalog-program"', count=21)
    assertNotContains(response, 'catalog-print')
    assertNotContains(response, 'events/pdf/')
    assertNotContains(response, 'pdf-catalog.css')
    assert [len(column) for column in response.context['index_columns']] == [10, 11]
    assertNotContains(response, 'Старая программа')
