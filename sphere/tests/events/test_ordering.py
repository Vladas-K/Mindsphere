from unittest.mock import patch

from django.contrib import admin
from django.test import RequestFactory
from django.urls import reverse
import pytest

from events.forms import EventForm
from events.models import Event
from events.ordering import catalog_position

pytestmark = pytest.mark.django_db


def save_form(employee, event=None, position=None, published=True, **extra):
    data = {'name': event.name if event else 'New', 'slug': event.slug if event else 'new', **extra}
    if published:
        data['is_published'] = 'on'
    if position is not None:
        data['sort_order'] = position
    form = EventForm(data=data, instance=event, user=employee)
    assert form.is_valid(), form.errors
    return form.save()


def assert_order(*events):
    rows = list(Event.objects.filter(is_published=True).values_list('pk', 'sort_order'))
    assert rows == [(event.pk, n) for n, event in enumerate(events, 1)]


def test_move_to_first_shifts_other_programs(employee, ordering):
    save_form(employee, ordering.c, 1)
    assert_order(ordering.c, ordering.a, ordering.b)
    ordering.hidden.refresh_from_db()
    assert ordering.hidden.sort_order == 0


def test_move_down_and_into_middle(employee, ordering):
    save_form(employee, ordering.a, 3)
    assert_order(ordering.b, ordering.c, ordering.a)
    save_form(employee, ordering.a, 2)
    assert_order(ordering.b, ordering.a, ordering.c)


def test_create_at_position_and_default_append(employee, ordering):
    new = save_form(employee, position=2)
    assert_order(ordering.a, new, ordering.b, ordering.c)
    last = save_form(employee, slug='last')
    assert_order(ordering.a, new, ordering.b, ordering.c, last)


def test_out_of_range_position_appends_and_zero_is_invalid(employee, ordering):
    save_form(employee, ordering.a, 999)
    assert_order(ordering.b, ordering.c, ordering.a)
    form = EventForm(data={'name': 'Invalid', 'sort_order': 0})
    assert not form.is_valid()
    assert 'sort_order' in form.errors


def test_initial_shows_actual_position_and_omission_keeps_it(employee, ordering):
    assert EventForm(instance=ordering.c).initial['sort_order'] == 3
    assert EventForm().initial['sort_order'] == 4
    save_form(employee, ordering.c)
    assert_order(ordering.a, ordering.b, ordering.c)


def test_hide_and_publish_insert_without_hidden_slots(employee, ordering):
    save_form(employee, ordering.b, 2, published=False)
    assert_order(ordering.a, ordering.c)
    assert catalog_position(ordering.b) is None
    save_form(employee, ordering.b, 1)
    assert_order(ordering.b, ordering.a, ordering.c)
    save_form(employee, ordering.hidden, 2)
    assert_order(ordering.b, ordering.hidden, ordering.a, ordering.c)


def test_commit_false_and_admin_save(employee, ordering):
    form = EventForm(data={'name': 'C', 'slug': 'c', 'sort_order': 1, 'is_published': 'on'}, instance=ordering.c)
    assert form.is_valid(), form.errors
    obj = form.save(commit=False)
    assert list(Event.objects.filter(is_published=True)) == [ordering.a, ordering.b, ordering.c]
    request = RequestFactory().post('/admin/events/event/')
    request.user = employee
    admin.site._registry[Event].save_model(request, obj, form, True)
    assert_order(ordering.c, ordering.a, ordering.b)


def test_reordering_rolls_back_if_bulk_update_fails(employee, ordering):
    before = list(Event.objects.values_list('pk', 'sort_order'))
    with patch('django.db.models.query.QuerySet.bulk_update', side_effect=RuntimeError('failure')):
        with pytest.raises(RuntimeError):
            save_form(employee, ordering.c, 1)
    assert list(Event.objects.values_list('pk', 'sort_order')) == before


def test_view_and_public_number_match_requested_position(client, employee, ordering):
    client.force_login(employee)
    response = client.post(reverse('events:event_edit', args=[ordering.c.slug]), {'name': ordering.c.name, 'slug': ordering.c.slug, 'sort_order': 1, 'is_published': 'on'})
    assert response.status_code == 302
    programs = client.get(reverse('events:index')).context['programs']
    assert [(p['event'].pk, p['number']) for p in programs] == [(ordering.c.pk, 1), (ordering.a.pk, 2), (ordering.b.pk, 3)]
