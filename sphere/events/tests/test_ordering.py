from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from events.forms import EventForm
from events.models import Event
from events.ordering import catalog_position


class CatalogPositionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='editor')
        # Existing catalogs may contain ties, zeros and gaps.
        self.a = Event.objects.create(name='A', slug='a', sort_order=0)
        self.b = Event.objects.create(name='B', slug='b', sort_order=1)
        self.c = Event.objects.create(name='C', slug='c', sort_order=1)
        self.hidden = Event.objects.create(name='Hidden', slug='hidden', sort_order=0, is_published=False)

    def save_form(self, event=None, position=None, published=True, **extra):
        data = {'name': event.name if event else 'New', 'slug': event.slug if event else 'new', **extra}
        if published:
            data['is_published'] = 'on'
        if position is not None:
            data['sort_order'] = position
        form = EventForm(data=data, instance=event, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        return form.save()

    def assert_order(self, *events):
        rows = list(Event.objects.filter(is_published=True).values_list('pk', 'sort_order'))
        self.assertEqual(rows, [(event.pk, n) for n, event in enumerate(events, 1)])

    def test_move_to_first_shifts_other_programs(self):
        self.save_form(self.c, 1)
        self.assert_order(self.c, self.a, self.b)
        self.hidden.refresh_from_db()
        self.assertEqual(self.hidden.sort_order, 0)

    def test_move_down_and_into_middle(self):
        self.save_form(self.a, 3)
        self.assert_order(self.b, self.c, self.a)
        self.save_form(self.a, 2)
        self.assert_order(self.b, self.a, self.c)

    def test_create_at_position_and_default_append(self):
        new = self.save_form(position=2)
        self.assert_order(self.a, new, self.b, self.c)
        last = self.save_form(slug='last')
        self.assert_order(self.a, new, self.b, self.c, last)

    def test_out_of_range_position_appends_and_zero_is_invalid(self):
        self.save_form(self.a, 999)
        self.assert_order(self.b, self.c, self.a)
        form = EventForm(data={'name': 'Invalid', 'sort_order': 0})
        self.assertFalse(form.is_valid())
        self.assertIn('sort_order', form.errors)

    def test_initial_shows_actual_position_and_omission_keeps_it(self):
        self.assertEqual(EventForm(instance=self.c).initial['sort_order'], 3)
        self.assertEqual(EventForm().initial['sort_order'], 4)
        self.save_form(self.c)
        self.assert_order(self.a, self.b, self.c)

    def test_hide_and_publish_insert_without_hidden_slots(self):
        self.save_form(self.b, 2, published=False)
        self.assert_order(self.a, self.c)
        self.assertIsNone(catalog_position(self.b))
        self.save_form(self.b, 1)
        self.assert_order(self.b, self.a, self.c)
        self.save_form(self.hidden, 2)
        self.assert_order(self.b, self.hidden, self.a, self.c)

    def test_commit_false_and_admin_save(self):
        form = EventForm(data={'name': 'C', 'slug': 'c', 'sort_order': 1, 'is_published': 'on'}, instance=self.c)
        self.assertTrue(form.is_valid(), form.errors)
        obj = form.save(commit=False)
        self.assertEqual(list(Event.objects.filter(is_published=True)), [self.a, self.b, self.c])
        request = RequestFactory().post('/admin/events/event/')
        request.user = self.user
        admin.site._registry[Event].save_model(request, obj, form, True)
        self.assert_order(self.c, self.a, self.b)

    def test_reordering_rolls_back_if_bulk_update_fails(self):
        before = list(Event.objects.values_list('pk', 'sort_order'))
        with patch('django.db.models.query.QuerySet.bulk_update', side_effect=RuntimeError('failure')):
            with self.assertRaises(RuntimeError):
                self.save_form(self.c, 1)
        self.assertEqual(list(Event.objects.values_list('pk', 'sort_order')), before)

    def test_view_and_public_number_match_requested_position(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('events:event_edit', args=[self.c.slug]), {
            'name': self.c.name, 'slug': self.c.slug, 'sort_order': 1, 'is_published': 'on',
        })
        self.assertEqual(response.status_code, 302)
        programs = self.client.get(reverse('events:index')).context['programs']
        self.assertEqual([(p['event'].pk, p['number']) for p in programs],
                         [(self.c.pk, 1), (self.a.pk, 2), (self.b.pk, 3)])
