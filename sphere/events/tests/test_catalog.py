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
from events.catalog import catalog_source, prepare_program


class PublicCatalogTests(TestCase):
    def test_image_guidance_and_optional_custom_caption(self):
        admin_user = get_user_model()(is_superuser=True)
        form = EventForm(user=admin_user)
        self.assertIn('1200 × 1252 px', form.fields['image'].help_text)
        self.assertIn('оставьте поле пустым', form.fields['slogan'].help_text)
        self.assertFalse(form.fields['slogan'].required)
        Event.objects.filter(pk=self.event.pk).update(image='events/custom.png', slogan=' ')
        response = self.client.get(reverse('events:index'))
        self.assertContains(response, 'program-art--custom')
        self.assertNotContains(response, '<figcaption')
        self.assertNotContains(response, 'class="program-art__mask"')
        Event.objects.filter(pk=self.event.pk).update(slogan='Наш слоган')
        self.assertContains(self.client.get(reverse('events:index')), '>Наш слоган</figcaption>')

    def test_number_colour_choices_are_saved_and_rendered(self):
        self.client.force_login(self.employee)
        for colour, ink in (('black', '#171717'), ('white', '#ffffff')):
            with self.subTest(colour=colour):
                response = self.client.post(reverse('events:event_create'), {
                    'name': 'Цвет ' + colour, 'slug': 'colour-' + colour,
                    'number_color': colour, 'is_published': 'on',
                })
                self.assertEqual(response.status_code, 302)
                event = Event.objects.get(slug='colour-' + colour)
                self.assertEqual(event.number_color, colour)
                self.assertEqual(prepare_program(event, 1, 1)['art_ink'], ink)
                event.image = 'events/example.png'
                event.save()
                self.assertContains(self.client.get(reverse('events:index')), '--art-ink: ' + ink)
                edit_url = reverse('events:event_edit', args=[event.slug])
                self.assertContains(self.client.get(edit_url), 'id="id_number_color"')
                response = self.client.post(edit_url, {
                    'name': event.name, 'slug': event.slug,
                    'number_color': 'black' if colour == 'white' else 'white',
                })
                self.assertEqual(response.status_code, 302)
                event.refresh_from_db()
                self.assertNotEqual(event.number_color, colour)

    def test_number_colour_preserves_legacy_palette_and_allows_override(self):
        row = next(row for row in catalog_source()['programs'] if row['catalog_page'] == 8)
        event = Event(name='Исходная', catalog_page=8, image=row['image'], number_color=None)
        self.assertEqual(prepare_program(event, 1, 1)['art_ink'], '#292929')
        self.assertEqual(EventForm(instance=event).initial['number_color'], 'black')
        form = EventForm(data={'name': event.name}, instance=event)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data['number_color'])
        event.number_color = 'white'
        self.assertEqual(prepare_program(event, 1, 1)['art_ink'], '#ffffff')

    def test_number_colour_field_has_two_choices_and_rejects_other_values(self):
        form = EventForm()
        self.assertEqual(list(form.fields['number_color'].choices), [('white', 'Белый'), ('black', 'Чёрный')])
        self.assertEqual(form.initial['number_color'], 'white')
        invalid = EventForm(data={'name': 'Программа', 'number_color': 'red'})
        self.assertFalse(invalid.is_valid())
        self.assertIn('number_color', invalid.errors)

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

    def test_cover_count_tracks_creating_hiding_and_deleting_programs(self):
        url = reverse('events:index')
        response = self.client.get(url)
        self.assertContains(response, 'class="cover-count" aria-hidden="true">1</div>')
        self.assertContains(response, '1 история, в которой главная роль — у вашей компании.')
        self.client.force_login(self.employee)
        response = self.client.post(reverse('events:event_create'), {
            'name': 'Новая программа', 'slug': 'new-program',
            'is_published': 'on', 'sort_order': '1',
        })
        self.assertRedirects(response, url)
        response = self.client.get(url)
        self.assertContains(response, 'class="cover-count" aria-hidden="true">2</div>')
        self.assertContains(response, '2 истории, в которых главная роль — у вашей компании.')
        self.assertTrue(all(program['total'] == 2 for program in response.context['programs']))
        event = Event.objects.get(slug='new-program')
        Event.objects.filter(pk=event.pk).update(is_published=False)
        self.assertEqual(self.client.get(url).context['catalog_total'], 1)
        event.delete()
        self.assertEqual(self.client.get(url).context['catalog_total'], 1)
        self.event.delete()
        self.assertContains(self.client.get(url), '0 историй, в которых главная роль — у вашей компании.')

    def test_cover_count_plural_forms_and_category_scope(self):
        url = reverse('events:index')
        for total, words in ((5, '5 историй'), (11, '11 историй'),
                             (21, '21 история'), (22, '22 истории')):
            with self.subTest(total=total):
                current = Event.objects.count()
                Event.objects.bulk_create([
                    Event(name=f'Программа {n}', slug=f'count-{n}')
                    for n in range(current, total)
                ])
                response = self.client.get(url)
                self.assertContains(response, 'class="cover-count" aria-hidden="true">' + str(total) + '</div>')
                self.assertContains(response, words + ', в котор')
                self.assertTrue(all(program['total'] == total for program in response.context['programs']))
        response = self.client.get(self.category.get_absolute_url())
        self.assertEqual(response.context['catalog_total'], 1)

    def test_contacts_arrow_links_to_catalog_index(self):
        response = self.client.get(reverse('events:index'))
        self.assertContains(response, '<a class="contact-catalog-back" href="#catalog" aria-label="К списку программ">')

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


    def test_html_catalog_has_no_limit_or_pdf_fallback_for_new_programs(self):
        Event.objects.bulk_create([
            Event(name=f'Новая программа {n}', slug=f'extended-{n}', sort_order=3)
            for n in range(30)
        ])
        response = self.client.get(reverse('events:index'))
        self.assertEqual(len(response.context['programs']), 31)
        self.assertEqual([len(column) for column in response.context['index_columns']], [15, 16])
        self.assertNotContains(response, 'catalog-print')
        self.assertContains(response, 'class="catalog-program catalog-program--no-image"', count=31)
        self.assertContains(response, '<h2>Новая программа 29</h2>')
        self.assertNotContains(response, 'events/pdf/graphics-04')

    def test_long_public_fields_render_once_in_html_without_pdf_line_breaks(self):
        name = 'Очень длинное название ' * 8
        summary = 'Подробное описание. ' * 100
        concept = 'Длинная характеристика ' * 80
        Event.objects.filter(pk=self.event.pk).update(
            name=name, short_description=summary, scenario=concept,
            image='events/new-custom.jpg', slogan='<script>caption()</script>',
        )
        response = self.client.get(reverse('events:index'))
        self.assertContains(response, '<h2>' + name + '</h2>', count=1)
        self.assertContains(response, '<p class="mobile-program__description">' + summary + '</p>', count=1)
        self.assertContains(response, '<dd>' + concept + '</dd>', count=1)
        self.assertContains(response, '&lt;script&gt;caption()&lt;/script&gt;', count=1)
        self.assertNotContains(response, '<script>caption()')
        self.assertNotContains(response, 'mobile-program__overlay')

    def test_detail_number_uses_catalog_position_instead_of_order_value(self):
        Event.objects.create(name='Первая по порядку', sort_order=0)
        Event.objects.filter(pk=self.event.pk).update(sort_order=50)
        self.client.force_login(self.employee)
        response = self.client.get(self.event.get_absolute_url())
        self.assertEqual(response.context['program']['number'], 2)

    def test_unpublished_card_has_status_instead_of_public_number(self):
        Event.objects.filter(pk=self.event.pk).update(
            is_published=False, image='events/hidden-program.png',
        )
        Event.objects.create(name='Опубликованная программа')
        self.client.force_login(self.employee)
        response = self.client.get(self.event.get_absolute_url())
        self.assertIsNone(response.context['program']['number'])
        self.assertContains(response, 'Не опубликовано')
        self.assertNotContains(response, 'class="program-art__number"')
        self.assertNotContains(response, 'Программа /')
        self.assertNotContains(response, '02 / 01')
        self.assertNotContains(self.client.get(reverse('events:index')), self.event.name)

    def test_long_edits_use_shared_html_without_legacy_layout(self):
        row = catalog_source()['programs'][0]
        Event.objects.filter(pk=self.event.pk).update(
            catalog_page=row['catalog_page'], image=row['image'],
            short_description='Длинное описание ' * 200,
        )
        response = self.client.get(reverse('events:index'))
        self.assertContains(response, '<p class="mobile-program__description">' + 'Длинное описание ' * 200 + '</p>', count=1)
        self.assertNotContains(response, 'catalog-print')
        self.assertNotContains(response, 'has-print-layout')

    def test_baked_caption_masks_only_apply_to_original_images(self):
        for page in (6, 16):
            with self.subTest(page=page):
                row = next(row for row in catalog_source()['programs'] if row['catalog_page'] == page)
                event = Event(catalog_page=page, image=row['image'])
                self.assertIsNotNone(prepare_program(event, 1, 1)['image_slogan_background'])
                self.assertEqual(prepare_program(event, 1, 1)['cassette_label'], page == 6)
                event.image = 'events/replacement.png'
                program = prepare_program(event, 1, 1)
                self.assertIsNone(program['image_slogan_background'])
                self.assertFalse(program['original_art'])
                self.assertFalse(program['cassette_label'])

    def test_blank_public_features_do_not_leave_empty_sections(self):
        Event.objects.filter(pk=self.event.pk).update(
            slogan=' ', short_description=' ', scenario=' ', program_format=' ',
        )
        response = self.client.get(reverse('events:index'))
        self.assertNotContains(response, '<details class="mobile-concept"')
        self.assertNotContains(response, 'class="mobile-program__specs"')
        self.assertNotContains(response, 'class="mobile-program__description"')

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
        self.assertContains(response, '<h2>Бурлеск</h2>')

    def test_complete_catalog_import_is_repeatable(self):
        with TemporaryDirectory(prefix='mindsphere-catalog-') as media:
            with override_settings(MEDIA_ROOT=media):
                for _ in range(2):
                    call_command('load_catalog', replace=True, stdout=StringIO())
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
                call_command('load_catalog', replace=True, stdout=StringIO())
                old.refresh_from_db()
                self.assertFalse(old.is_published)
                response = self.client.get(reverse('events:index'))
                self.assertContains(response, 'class="catalog-page program-sheet"', count=21)
                self.assertContains(response, 'class="catalog-program"', count=21)
                self.assertNotContains(response, 'catalog-print')
                self.assertNotContains(response, 'events/pdf/')
                self.assertNotContains(response, 'pdf-catalog.css')
                self.assertEqual([len(column) for column in response.context['index_columns']], [10, 11])
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
