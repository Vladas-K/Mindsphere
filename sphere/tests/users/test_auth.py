from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects
import pytest

from events.models import Event

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('catalog_event', 'employee')]


def test_login_page_has_accessible_fields_and_no_registration(client):
    response = client.get(reverse('users:login'))
    assertContains(response, 'Вход для')
    assertContains(response, 'autocomplete="username"')
    assertContains(response, 'autocomplete="current-password"')
    assertContains(response, 'aria-controls="id_password"')
    assertNotContains(response, 'Зарегистрироваться')


def test_successful_login_shows_employee_navigation(client):
    response = client.post(reverse('users:login'), {'username': 'employee', 'password': 'Employee-test-password'})
    assertRedirects(response, reverse('events:index'))
    response = client.get(reverse('events:index'))
    for text in ('Анна', 'Добавить программу', 'Изменить пароль', 'Выйти', 'Подробнее'):
        assertContains(response, text)
    assertNotContains(response, 'Вход для сотрудников')


def test_login_returns_to_requested_card(catalog_event, client):
    target = catalog_event.get_absolute_url()
    response = client.get(reverse('users:login'), {'next': target})
    assertContains(response, 'name="next" value="' + target + '"')
    response = client.post(reverse('users:login'), {'username': 'employee', 'password': 'Employee-test-password', 'next': target})
    assertRedirects(response, target)
    assertContains(client.get(target), catalog_event.description)


def test_external_next_does_not_redirect_outside_site(client):
    response = client.post(reverse('users:login'), {'username': 'employee', 'password': 'Employee-test-password', 'next': 'https://example.org/'})
    assertRedirects(response, reverse('events:index'))


def test_invalid_credentials_preserve_login_and_destination(catalog_event, client):
    target = catalog_event.get_absolute_url()
    response = client.post(reverse('users:login'), {'username': 'employee', 'password': 'Wrong-password', 'next': target})
    assertContains(response, 'Не удалось войти.')
    assertContains(response, 'value="employee"')
    assertContains(response, 'name="next" value="' + target + '"')
    assertNotContains(response, 'Wrong-password')
    assert '_auth_user_id' not in client.session


def test_inactive_account_cannot_login(client, employee):
    employee.is_active = False
    employee.save(update_fields=['is_active'])
    response = client.post(reverse('users:login'), {'username': 'employee', 'password': 'Employee-test-password'})
    assertContains(response, 'Не удалось войти.')
    assert '_auth_user_id' not in client.session


def test_logout_restores_guest_navigation_and_closes_card(catalog_event, client, employee):
    client.force_login(employee)
    response = client.post(reverse('users:logout'))
    assert response.status_code == 200
    response = client.get(reverse('events:index'))
    assertNotContains(response, 'Вход для сотрудников')
    assertNotContains(response, 'Добавить программу')
    assert client.get(catalog_event.get_absolute_url()).status_code == 302


def test_guest_pages_do_not_advertise_employee_access(client):
    response = client.get(reverse('events:index'))
    assertNotContains(response, reverse('users:login'))
    assertNotContains(response, 'staff-bar')
    assertNotContains(response, 'Вход для сотрудников')


@pytest.mark.parametrize('old,new,confirmation,invalid_field', [
    ('Wrong-current-password', 'New-employee-password-82', 'New-employee-password-82', 'old_password'),
    ('Employee-test-password', 'New-employee-password-82', 'Different-password-93', 'new_password2'),
    ('Employee-test-password', '123', '123', 'new_password2'),
], ids=['wrong-current-password', 'mismatched-passwords', 'weak-password'])
def test_password_change_errors_are_visible_and_password_is_unchanged(
    client, employee, old, new, confirmation, invalid_field,
):
    client.force_login(employee)
    response = client.post(reverse('users:password_change'), {
        'old_password': old, 'new_password1': new, 'new_password2': confirmation,
    })
    assert response.status_code == 200
    form = response.context['form']
    assert invalid_field in form.errors
    for errors in form.errors.values():
        for error in errors:
            assertContains(response, error)
    assertContains(response, 'aria-invalid="true"')
    assertContains(response, invalid_field + '_error')
    assertContains(response, 'autocomplete="current-password"')
    assertContains(response, 'autocomplete="new-password"')
    assertNotContains(response, 'value="' + new + '"')
    assertNotContains(response, 'cdn.jsdelivr.net')
    employee.refresh_from_db()
    assert employee.check_password('Employee-test-password')


def test_password_change_preserves_session_and_uses_new_password(catalog_event, client, employee):
    client.force_login(employee)
    response = client.post(reverse('users:password_change'), {'old_password': 'Employee-test-password', 'new_password1': 'New-employee-password-82', 'new_password2': 'New-employee-password-82'})
    assertRedirects(response, reverse('users:password_change_done'))
    assertContains(client.get(reverse('users:password_change_done')), 'Вернуться в каталог')
    assert client.get(catalog_event.get_absolute_url()).status_code == 200
    employee.refresh_from_db()
    assert employee.check_password('New-employee-password-82')
    assert not employee.check_password('Employee-test-password')
    client.logout()
    assert client.login(username='employee', password='New-employee-password-82')


def test_logout_has_navigation_and_local_styles(client, employee):
    client.force_login(employee)
    assert client.get(reverse('users:logout')).status_code == 405
    response = client.post(reverse('users:logout'))
    for text in ('Войти снова', reverse('users:login'), 'users/staff.css'):
        assertContains(response, text)
    assertNotContains(response, 'cdn.jsdelivr.net')
    assert '_auth_user_id' not in client.session


def test_delete_requires_confirmation_and_has_cancel_link(catalog_event, client, employee):
    url = reverse('events:event_delete', kwargs={'slug': catalog_event.slug})
    assert client.get(url).status_code == 302
    assert client.post(url).status_code == 302
    client.force_login(employee)
    response = client.get(url)
    assertContains(response, 'Отмена')
    assertContains(response, 'href="' + catalog_event.get_absolute_url() + '"')
    assertNotContains(response, 'cdn.jsdelivr.net')
    assert Event.objects.filter(pk=catalog_event.pk).exists()
    response = client.post(url)
    assertRedirects(response, reverse('events:index'))
    assert not Event.objects.filter(pk=catalog_event.pk).exists()


def test_password_pages_require_login(client):
    for name in ('users:password_change', 'users:password_change_done'):
        assert client.get(reverse(name)).status_code == 302


@pytest.mark.parametrize('path', [
    '/auth/signup/', '/auth/password_reset/', '/auth/password_reset/done/',
    '/auth/reset/MQ/example-token/', '/auth/reset/done/',
])
@pytest.mark.parametrize('method', ['get', 'post'])
def test_registration_and_email_password_reset_are_not_available(client, path, method):
    assert getattr(client, method)(path).status_code == 404
