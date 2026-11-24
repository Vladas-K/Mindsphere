from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.management import call_command
from django.test import override_settings
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from events.forms import EventForm
from events.models import Category, Event
from events.catalog import catalog_source


class PublicCatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Программы', slug='programs')
        cls.event = Event.objects.create(
            name='Бурлеск', slug='burlesque', category=cls.category,
            short_description='Публичное описание программы.',
            description='ВНУТРЕННИЙ СЦЕНАРИЙ, ТОЛЬКО ДЛЯ КОМАНДЫ',
            slogan='Шоу, которое не скроет эмоций', scenario='Музыкальный спектакль',
            program_format='Музыкальный вечер', sort_order=2,
        )
        cls.employee = get_user_model().objects.create_user(username='employee')

    def test_public_catalog_does_not_expose_internal_content_or_links(self):
        for url in (reverse('events:index'), self.category.get_absolute_url()):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, self.event.short_description)
                self.assertContains(response, self.event.slogan)
                self.assertContains(response, self.event.scenario)
                self.assertContains(response, self.event.program_format)
                self.assertContains(response, '#program-' + str(self.event.pk))
                self.assertNotContains(response, self.event.description)
                self.assertNotContains(response, 'Подробнее')
                self.assertNotContains(response, self.event.get_absolute_url())
                self.assertNotContains(response, 'Интерактивы')

    def test_all_programs_are_visible_in_manual_order(self):
        first = Event.objects.create(name='Первая', description='private', sort_order=1)
        Event.objects.bulk_create([
            Event(name=f'Программа {n}', slug=f'program-{n}', description='private', sort_order=3)
            for n in range(6)
        ])
        response = self.client.get(reverse('events:index'))
        self.assertEqual(len(response.context['event_list']), 8)
        self.assertEqual(response.context['event_list'][0], first)
        self.assertContains(response, 'Программа 5')
        self.assertFalse(response.context['is_paginated'])

    def test_empty_summary_does_not_fall_back_to_private_description(self):
        Event.objects.filter(pk=self.event.pk).update(short_description='')
        response = self.client.get(reverse('events:index'))
        self.assertNotContains(response, self.event.description)

    def test_mobile_presentation_has_public_concept_and_contact_actions(self):
        response = self.client.get(reverse('events:index'))
        self.assertContains(response, '<summary>Что входит в концепцию')
        self.assertContains(response, 'class="mobile-program__specs"')
        self.assertContains(response, 'href="tel:+79118371723"')
        self.assertContains(response, 'class="mobile-catalog-back" href="#catalog" aria-label="К списку программ" hidden')
        self.assertNotContains(response, self.event.description)

    def test_mobile_text_uses_live_fields_instead_of_source_pdf_copy(self):
        Event.objects.filter(pk=self.event.pk).update(
            short_description='Новое публичное описание для телефона',
            scenario='Новая концепция для каталога',
        )
        response = self.client.get(reverse('events:index'))
        self.assertContains(response, '<p class="mobile-program__description">Новое публичное описание для телефона</p>')
        self.assertContains(response, '<dd>Новая концепция для каталога</dd>')
        self.assertNotContains(response, self.event.description)

    def test_invalid_editor_preserves_draft_and_associates_field_errors(self):
        self.client.force_login(self.employee)
        count = Event.objects.count()
        response = self.client.post(reverse('events:event_create'), {
            'name': '', 'slug': 'invalid slug', 'is_published': 'on',
            'short_description': 'Сохранённый черновик описания',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Сохранённый черновик описания')
        self.assertContains(response, 'href="#id_name"')
        self.assertContains(response, 'id="id_name_error"')
        self.assertContains(response, 'aria-describedby="id_name_helptext id_name_error"')
        self.assertContains(response, 'aria-invalid="true"')
        self.assertContains(response, 'type="checkbox" name="is_published"')
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertNotContains(response, 'cdn.jsdelivr.net')
        self.assertEqual(Event.objects.count(), count)

    def test_empty_internal_description_offers_edit_link(self):
        self.client.force_login(self.employee)
        for text in ('', ' \n '):
            with self.subTest(description=text):
                Event.objects.filter(pk=self.event.pk).update(description=text)
                response = self.client.get(self.event.get_absolute_url())
                self.assertContains(response, 'Полное описание пока не добавлено.')
                self.assertContains(response, 'Добавить описание')
                self.assertContains(response, reverse('events:event_edit', args=[self.event.slug]) + '#id_description')
                self.assertContains(response, reverse('events:event_delete', args=[self.event.slug]))
                self.assertNotContains(response, 'cdn.jsdelivr.net')

    def test_internal_description_preserves_line_breaks_and_escapes_html(self):
        self.client.force_login(self.employee)
        Event.objects.filter(pk=self.event.pk).update(description='Первая строка\n<script>private()</script>')
        response = self.client.get(self.event.get_absolute_url())
        self.assertContains(response, 'Первая строка<br>&lt;script&gt;private()&lt;/script&gt;')
        self.assertNotContains(response, '<script>private()')
        self.assertContains(response, 'Редактировать описание')
        self.assertNotContains(response, 'Полное описание пока не добавлено.')

    def test_unpublished_program_is_not_in_public_catalog(self):
        Event.objects.filter(pk=self.event.pk).update(is_published=False)
        response = self.client.get(reverse('events:index'))
        self.assertNotContains(response, self.event.name)
        self.assertNotContains(response, '#program-' + str(self.event.pk))

    def test_public_page_has_no_staff_navigation_or_filters(self):
        response = self.client.get(reverse('events:index'))
        self.assertNotContains(response, 'Вход для сотрудников')
        self.assertNotContains(response, reverse('users:login'))
        self.assertNotContains(response, 'staff-bar')
        self.assertNotContains(response, 'Категории программ')
        self.assertNotContains(response, 'site-header')
        self.assertContains(response, 'viewBox="0 0 1200 675"')

    def test_complete_pdf_catalog_import_is_repeatable(self):
        with TemporaryDirectory(prefix='mindsphere-catalog-') as media:
            with override_settings(MEDIA_ROOT=media):
                for _ in range(2):
                    call_command('load_pdf_catalog', replace=True, stdout=StringIO())
                active = Event.objects.filter(is_published=True)
                expected = catalog_source()['programs']
                self.assertEqual(active.count(), 21)
                self.assertEqual(list(active.values_list('name', flat=True)), [r['name'] for r in expected])
                self.assertEqual(Event.objects.get(pk=self.event.pk).description, self.event.description)
                self.assertEqual(get_user_model().objects.count(), 1)
                for event, row in zip(active, expected):
                    self.assertEqual(event.catalog_page, row['catalog_page'])
                    self.assertEqual(event.short_description, row['short_description'])
                    self.assertTrue(Path(event.image.path).is_file())
                old = Event.objects.create(name='Старая программа', description='private')
                call_command('load_pdf_catalog', replace=True, stdout=StringIO())
                old.refresh_from_db()
                self.assertFalse(old.is_published)
                response = self.client.get(reverse('events:index'))
                self.assertContains(response, 'class="pdf-page program-sheet"', count=21)
                self.assertContains(response, 'class="mobile-program mobile-only"', count=21)
                self.assertNotContains(response, 'Старая программа')

    def test_guests_cannot_open_or_modify_internal_cards(self):
        for name in ('event_detail', 'event_edit', 'event_delete'):
            url = reverse('events:' + name, args=[self.event.slug])
            for method in ('get', 'post'):
                with self.subTest(name=name, method=method):
                    response = getattr(self.client, method)(url)
                    self.assertRedirects(response, reverse('users:login') + '?next=' + url)
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())

    def test_employee_can_open_card_and_edit_public_fields(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse('events:index'))
        self.assertContains(response, 'Подробнее')
        self.assertNotContains(response, self.event.description)
        response = self.client.get(self.event.get_absolute_url())
        self.assertContains(response, self.event.description)
        response = self.client.post(
            reverse('events:event_edit', args=[self.event.slug]),
            data={
                'name': self.event.name, 'slug': self.event.slug,
                'description': self.event.description, 'short_description': 'Новый анонс',
                'scenario': 'Новый сценарий', 'sort_order': 4,
            },
        )
        self.assertRedirects(response, reverse('events:index'))
        self.event.refresh_from_db()
        self.assertEqual(self.event.short_description, 'Новый анонс')
        self.assertEqual(self.event.scenario, 'Новый сценарий')
        self.assertEqual(self.event.sort_order, 4)
        self.assertEqual(self.event.description, 'ВНУТРЕННИЙ СЦЕНАРИЙ, ТОЛЬКО ДЛЯ КОМАНДЫ')

    def test_editor_escapes_public_text_and_rejects_negative_order(self):
        Event.objects.filter(pk=self.event.pk).update(short_description='<script>alert(1)</script>')
        response = self.client.get(reverse('events:index'))
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        form = EventForm(data={'name': 'Программа', 'description': 'Описание', 'sort_order': -1})
        self.assertFalse(form.is_valid())
        self.assertIn('sort_order', form.errors)
