from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from events.forms import EventForm
from events.models import Event


class SloganPermissionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.employee = get_user_model().objects.create_user(username='writer')
        cls.superuser = get_user_model().objects.create_superuser(username='owner')
        cls.event = Event.objects.create(name='Программа', slug='program', slogan='Прежний слоган')

    def test_employee_cannot_change_slogan_through_create_or_edit(self):
        self.client.force_login(self.employee)
        create_url = reverse('events:event_create')
        edit_url = reverse('events:event_edit', args=[self.event.slug])
        for url in (create_url, edit_url):
            self.assertNotContains(self.client.get(url), 'id="id_slogan"')
            self.assertContains(self.client.get(url), 'со встроенным слоганом')
        response = self.client.post(create_url, {
            'name': 'Новая', 'slug': 'new', 'slogan': 'Подставленный слоган',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Event.objects.get(slug='new').slogan, '')
        response = self.client.post(edit_url, {
            'name': 'Изменённое название', 'slug': self.event.slug, 'slogan': 'Подмена',
        })
        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.slogan, 'Прежний слоган')
        self.assertEqual(self.event.name, 'Изменённое название')

    def test_superuser_can_create_edit_and_clear_slogan(self):
        self.client.force_login(self.superuser)
        create_url = reverse('events:event_create')
        self.assertContains(self.client.get(create_url), 'id="id_slogan"')
        self.assertContains(self.client.get(create_url), 'только суперпользователю')
        self.client.post(create_url, {'name': 'Новая', 'slug': 'new', 'slogan': 'Новый слоган'})
        self.assertEqual(Event.objects.get(slug='new').slogan, 'Новый слоган')
        edit_url = reverse('events:event_edit', args=[self.event.slug])
        self.assertContains(self.client.get(edit_url), 'id="id_slogan"')
        for slogan in ('Изменённый слоган', ''):
            response = self.client.post(edit_url, {
                'name': self.event.name, 'slug': self.event.slug, 'slogan': slogan,
            })
            self.assertEqual(response.status_code, 302)
            self.event.refresh_from_db()
            self.assertEqual(self.event.slogan, slogan)

    def test_admin_uses_same_superuser_restriction(self):
        model_admin = admin.site._registry[Event]
        for user, allowed in ((self.employee, False), (self.superuser, True)):
            with self.subTest(allowed=allowed):
                request = RequestFactory().get('/admin/events/event/add/')
                request.user = user
                form = model_admin.get_form(request)()
                self.assertEqual('slogan' in form.fields, allowed)
                names = [name for _, options in model_admin.get_fieldsets(request)
                         for name in options['fields']]
                self.assertEqual('slogan' in names, allowed)
        self.employee.is_staff = True
        self.assertNotIn('slogan', EventForm(user=self.employee).fields)
        self.assertNotIn('slogan', EventForm().fields)
