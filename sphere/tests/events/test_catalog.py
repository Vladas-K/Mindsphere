from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects
import pytest

from events.catalog import catalog_source, prepare_program
from events.models import Event

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('catalog_event', 'employee')]


def test_event_in_list(catalog_event, client):
    response = client.get(reverse('events:index'))
    assert catalog_event in response.context['object_list']


def test_cover_count_tracks_creating_hiding_and_deleting_programs(catalog_event, client, employee):
    url = reverse('events:index')
    response = client.get(url)
    assertContains(response, 'class="cover-count" aria-hidden="true">1</div>')
    assertContains(response, '1 история, в которой главная роль — у вашей компании.')
    client.force_login(employee)
    response = client.post(reverse('events:event_create'), {'name': 'Новая программа', 'slug': 'new-program', 'is_published': 'on', 'sort_order': '1'})
    assertRedirects(response, url)
    response = client.get(url)
    assertContains(response, 'class="cover-count" aria-hidden="true">2</div>')
    assertContains(response, '2 истории, в которых главная роль — у вашей компании.')
    assert all((program['total'] == 2 for program in response.context['programs']))
    event = Event.objects.get(slug='new-program')
    Event.objects.filter(pk=event.pk).update(is_published=False)
    assert client.get(url).context['catalog_total'] == 1
    event.delete()
    assert client.get(url).context['catalog_total'] == 1
    catalog_event.delete()
    assertContains(client.get(url), '0 историй, в которых главная роль — у вашей компании.')


def test_cover_count_plural_forms_and_category_scope(category, client):
    url = reverse('events:index')
    for total, words in ((5, '5 историй'), (11, '11 историй'), (21, '21 история'), (22, '22 истории')):
        current = Event.objects.count()
        Event.objects.bulk_create([Event(name=f'Программа {n}', slug=f'count-{n}') for n in range(current, total)])
        response = client.get(url)
        assertContains(response, 'class="cover-count" aria-hidden="true">' + str(total) + '</div>')
        assertContains(response, words + ', в котор')
        assert all((program['total'] == total for program in response.context['programs']))
    response = client.get(category.get_absolute_url())
    assert response.context['catalog_total'] == 1


def test_contacts_arrow_links_to_catalog_index(client):
    response = client.get(reverse('events:index'))
    assertContains(response, '<a class="contact-catalog-back" href="#catalog" aria-label="К списку программ">')


def test_all_programs_are_visible_in_manual_order(client):
    first = Event.objects.create(name='Первая', description='private', sort_order=1)
    Event.objects.bulk_create([Event(name=f'Программа {n}', slug=f'program-{n}', description='private', sort_order=3) for n in range(6)])
    response = client.get(reverse('events:index'))
    assert len(response.context['event_list']) == 8
    assert response.context['event_list'][0] == first
    assertContains(response, 'Программа 5')
    assert not response.context['is_paginated']


def test_mobile_presentation_has_public_concept_and_contact_actions(catalog_event, client):
    response = client.get(reverse('events:index'))
    assertContains(response, '<summary>Что входит в концепцию')
    assertContains(response, 'class="mobile-program__specs"')
    assertContains(response, 'href="tel:+79118371723"')
    assertContains(response, 'class="mobile-catalog-back" href="#catalog" aria-label="К списку программ" hidden')
    assertNotContains(response, catalog_event.description)


def test_mobile_text_uses_live_fields_instead_of_source_pdf_copy(catalog_event, client):
    Event.objects.filter(pk=catalog_event.pk).update(short_description='Новое публичное описание для телефона', scenario='Новая концепция для каталога')
    response = client.get(reverse('events:index'))
    assertContains(response, '<p class="mobile-program__description">Новое публичное описание для телефона</p>')
    assertContains(response, '<dd>Новая концепция для каталога</dd>')
    assertNotContains(response, catalog_event.description)


def test_html_catalog_has_no_limit_or_pdf_fallback_for_new_programs(client):
    Event.objects.bulk_create([Event(name=f'Новая программа {n}', slug=f'extended-{n}', sort_order=3) for n in range(30)])
    response = client.get(reverse('events:index'))
    assert len(response.context['programs']) == 31
    assert [len(column) for column in response.context['index_columns']] == [15, 16]
    assertNotContains(response, 'catalog-print')
    assertContains(response, 'class="catalog-program catalog-program--no-image"', count=31)
    assertContains(response, '<h2>Новая программа 29</h2>')
    assertNotContains(response, 'events/pdf/graphics-04')


def test_long_public_fields_render_once_in_html_without_pdf_line_breaks(catalog_event, client):
    name = 'Очень длинное название ' * 8
    summary = 'Подробное описание. ' * 100
    concept = 'Длинная характеристика ' * 80
    Event.objects.filter(pk=catalog_event.pk).update(name=name, short_description=summary, scenario=concept, image='events/new-custom.jpg', slogan='<script>caption()</script>')
    response = client.get(reverse('events:index'))
    assertContains(response, '<h2>' + name + '</h2>', count=1)
    assertContains(response, '<p class="mobile-program__description">' + summary + '</p>', count=1)
    assertContains(response, '<dd>' + concept + '</dd>', count=1)
    assertContains(response, '&lt;script&gt;caption()&lt;/script&gt;', count=1)
    assertNotContains(response, '<script>caption()')
    assertNotContains(response, 'mobile-program__overlay')


def test_detail_number_uses_catalog_position_instead_of_order_value(catalog_event, client, employee):
    Event.objects.create(name='Первая по порядку', sort_order=0)
    Event.objects.filter(pk=catalog_event.pk).update(sort_order=50)
    client.force_login(employee)
    response = client.get(catalog_event.get_absolute_url())
    assert response.context['program']['number'] == 2


def test_unpublished_card_has_status_instead_of_public_number(catalog_event, client, employee):
    Event.objects.filter(pk=catalog_event.pk).update(is_published=False, image='events/hidden-program.png')
    Event.objects.create(name='Опубликованная программа')
    client.force_login(employee)
    response = client.get(catalog_event.get_absolute_url())
    assert response.context['program']['number'] is None
    assertContains(response, 'Не опубликовано')
    assertNotContains(response, 'class="program-art__number"')
    assertNotContains(response, 'Программа /')
    assertNotContains(response, '02 / 01')
    assertNotContains(client.get(reverse('events:index')), catalog_event.name)


def test_long_edits_use_shared_html_without_legacy_layout(catalog_event, client):
    row = catalog_source()['programs'][0]
    Event.objects.filter(pk=catalog_event.pk).update(catalog_page=row['catalog_page'], image=row['image'], short_description='Длинное описание ' * 200)
    response = client.get(reverse('events:index'))
    assertContains(response, '<p class="mobile-program__description">' + 'Длинное описание ' * 200 + '</p>', count=1)
    assertNotContains(response, 'catalog-print')
    assertNotContains(response, 'has-print-layout')


def test_baked_caption_masks_only_apply_to_original_images():
    for page in (6, 16):
        row = next((row for row in catalog_source()['programs'] if row['catalog_page'] == page))
        event = Event(catalog_page=page, image=row['image'])
        assert prepare_program(event, 1, 1)['image_slogan_background'] is not None
        assert prepare_program(event, 1, 1)['cassette_label'] == (page == 6)
        event.image = 'events/replacement.png'
        program = prepare_program(event, 1, 1)
        assert program['image_slogan_background'] is None
        assert not program['original_art']
        assert not program['cassette_label']


def test_blank_public_features_do_not_leave_empty_sections(catalog_event, client):
    Event.objects.filter(pk=catalog_event.pk).update(slogan=' ', short_description=' ', scenario=' ', program_format=' ')
    response = client.get(reverse('events:index'))
    assertNotContains(response, '<details class="mobile-concept"')
    assertNotContains(response, 'class="mobile-program__specs"')
    assertNotContains(response, 'class="mobile-program__description"')


def test_unpublished_program_is_not_in_public_catalog(catalog_event, client):
    Event.objects.filter(pk=catalog_event.pk).update(is_published=False)
    response = client.get(reverse('events:index'))
    assertNotContains(response, catalog_event.name)
    assertNotContains(response, '#program-' + str(catalog_event.pk))
