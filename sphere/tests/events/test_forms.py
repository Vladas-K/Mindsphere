from django.contrib.auth import get_user_model
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects
import pytest

from events.catalog import catalog_source, prepare_program
from events.forms import EventForm
from events.models import Event

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('catalog_event', 'employee')]


def test_image_guidance_and_optional_custom_caption(catalog_event, client):
    admin_user = get_user_model()(is_superuser=True)
    form = EventForm(user=admin_user)
    assert '1200 × 1252 px' in form.fields['image'].help_text
    assert 'оставьте поле пустым' in form.fields['slogan'].help_text
    assert not form.fields['slogan'].required
    Event.objects.filter(pk=catalog_event.pk).update(image='events/custom.png', slogan=' ')
    response = client.get(reverse('events:index'))
    assertContains(response, 'program-art--custom')
    assertNotContains(response, '<figcaption')
    assertNotContains(response, 'class="program-art__mask"')
    Event.objects.filter(pk=catalog_event.pk).update(slogan='Наш слоган')
    assertContains(client.get(reverse('events:index')), '>Наш слоган</figcaption>')


def test_number_colour_choices_are_saved_and_rendered(client, employee):
    client.force_login(employee)
    for colour, ink in (('black', '#171717'), ('white', '#ffffff')):
        response = client.post(reverse('events:event_create'), {'name': 'Цвет ' + colour, 'slug': 'colour-' + colour, 'number_color': colour, 'is_published': 'on'})
        assert response.status_code == 302
        event = Event.objects.get(slug='colour-' + colour)
        assert event.number_color == colour
        assert prepare_program(event, 1, 1)['art_ink'] == ink
        event.image = 'events/example.png'
        event.save()
        assertContains(client.get(reverse('events:index')), '--art-ink: ' + ink)
        edit_url = reverse('events:event_edit', args=[event.slug])
        assertContains(client.get(edit_url), 'id="id_number_color"')
        response = client.post(edit_url, {'name': event.name, 'slug': event.slug, 'number_color': 'black' if colour == 'white' else 'white'})
        assert response.status_code == 302
        event.refresh_from_db()
        assert event.number_color != colour


def test_number_colour_preserves_legacy_palette_and_allows_override():
    row = next((row for row in catalog_source()['programs'] if row['catalog_page'] == 8))
    event = Event(name='Исходная', catalog_page=8, image=row['image'], number_color=None)
    assert prepare_program(event, 1, 1)['art_ink'] == '#292929'
    assert EventForm(instance=event).initial['number_color'] == 'black'
    form = EventForm(data={'name': event.name}, instance=event)
    assert form.is_valid(), form.errors
    assert form.cleaned_data['number_color'] is None
    event.number_color = 'white'
    assert prepare_program(event, 1, 1)['art_ink'] == '#ffffff'


def test_number_colour_field_has_two_choices_and_rejects_other_values():
    form = EventForm()
    assert list(form.fields['number_color'].choices) == [('white', 'Белый'), ('black', 'Чёрный')]
    assert form.initial['number_color'] == 'white'
    invalid = EventForm(data={'name': 'Программа', 'number_color': 'red'})
    assert not invalid.is_valid()
    assert 'number_color' in invalid.errors


def test_invalid_editor_preserves_draft_and_associates_field_errors(client, employee):
    client.force_login(employee)
    count = Event.objects.count()
    response = client.post(reverse('events:event_create'), {'name': '', 'slug': 'invalid slug', 'is_published': 'on', 'short_description': 'Сохранённый черновик описания'})
    assert response.status_code == 200
    assertContains(response, 'Сохранённый черновик описания')
    assertContains(response, 'href="#id_name"')
    assertContains(response, 'id="id_name_error"')
    assertContains(response, 'aria-describedby="id_name_helptext id_name_error"')
    assertContains(response, 'aria-invalid="true"')
    assertContains(response, 'type="checkbox" name="is_published"')
    assertContains(response, 'enctype="multipart/form-data"')
    assertNotContains(response, 'cdn.jsdelivr.net')
    assert Event.objects.count() == count


def test_employee_can_open_card_and_edit_public_fields(catalog_event, client, employee):
    client.force_login(employee)
    response = client.get(reverse('events:index'))
    assertContains(response, 'Подробнее')
    assertNotContains(response, catalog_event.description)
    response = client.get(catalog_event.get_absolute_url())
    assertContains(response, catalog_event.description)
    response = client.post(reverse('events:event_edit', args=[catalog_event.slug]), data={'name': catalog_event.name, 'slug': catalog_event.slug, 'description': catalog_event.description, 'short_description': 'Новый анонс', 'scenario': 'Новый сценарий', 'sort_order': 4})
    assertRedirects(response, reverse('events:index'))
    catalog_event.refresh_from_db()
    assert catalog_event.short_description == 'Новый анонс'
    assert catalog_event.scenario == 'Новый сценарий'
    assert catalog_event.sort_order == 4
    assert catalog_event.description == 'ВНУТРЕННИЙ СЦЕНАРИЙ, ТОЛЬКО ДЛЯ КОМАНДЫ'


def test_editor_escapes_public_text_and_rejects_negative_order(catalog_event, client):
    Event.objects.filter(pk=catalog_event.pk).update(short_description='<script>alert(1)</script>')
    response = client.get(reverse('events:index'))
    assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
    assertNotContains(response, '<script>alert(1)</script>')
    form = EventForm(data={'name': 'Программа', 'description': 'Описание', 'sort_order': -1})
    assert not form.is_valid()
    assert 'sort_order' in form.errors
