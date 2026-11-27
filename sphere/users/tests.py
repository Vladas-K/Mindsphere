from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from events.models import Event


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class EmployeeLoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.employee = get_user_model().objects.create_user(
            username='employee', password='Employee-test-password', first_name='Анна',
        )
        cls.event = Event.objects.create(name='Программа', description='Внутренние материалы')

    def test_login_page_has_accessible_fields_and_no_registration(self):
        response = self.client.get(reverse('users:login'))
        self.assertContains(response, 'Вход для')
        self.assertContains(response, 'autocomplete="username"')
        self.assertContains(response, 'autocomplete="current-password"')
        self.assertContains(response, 'aria-controls="id_password"')
        self.assertNotContains(response, 'Зарегистрироваться')

    def test_successful_login_shows_employee_navigation(self):
        response = self.client.post(reverse('users:login'), {
            'username': 'employee', 'password': 'Employee-test-password',
        })
        self.assertRedirects(response, reverse('events:index'))
        response = self.client.get(reverse('events:index'))
        for text in ('Анна', 'Добавить программу', 'Изменить пароль', 'Выйти', 'Подробнее'):
            self.assertContains(response, text)
        self.assertNotContains(response, 'Вход для сотрудников')

    def test_login_returns_to_requested_card(self):
        target = self.event.get_absolute_url()
        response = self.client.get(reverse('users:login'), {'next': target})
        self.assertContains(response, 'name="next" value="' + target + '"')
        response = self.client.post(reverse('users:login'), {
            'username': 'employee', 'password': 'Employee-test-password', 'next': target,
        })
        self.assertRedirects(response, target)
        self.assertContains(self.client.get(target), self.event.description)

    def test_external_next_does_not_redirect_outside_site(self):
        response = self.client.post(reverse('users:login'), {
            'username': 'employee', 'password': 'Employee-test-password',
            'next': 'https://example.org/',
        })
        self.assertRedirects(response, reverse('events:index'))

    def test_invalid_credentials_preserve_login_and_destination(self):
        target = self.event.get_absolute_url()
        response = self.client.post(reverse('users:login'), {
            'username': 'employee', 'password': 'Wrong-password', 'next': target,
        })
        self.assertContains(response, 'Не удалось войти.')
        self.assertContains(response, 'value="employee"')
        self.assertContains(response, 'name="next" value="' + target + '"')
        self.assertNotContains(response, 'Wrong-password')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_inactive_account_cannot_login(self):
        self.employee.is_active = False
        self.employee.save(update_fields=['is_active'])
        response = self.client.post(reverse('users:login'), {
            'username': 'employee', 'password': 'Employee-test-password',
        })
        self.assertContains(response, 'Не удалось войти.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_restores_guest_navigation_and_closes_card(self):
        self.client.force_login(self.employee)
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('events:index'))
        self.assertNotContains(response, 'Вход для сотрудников')
        self.assertNotContains(response, 'Добавить программу')
        self.assertEqual(self.client.get(self.event.get_absolute_url()).status_code, 302)

    def test_guest_pages_do_not_advertise_employee_access(self):
        response = self.client.get(reverse('events:index'))
        self.assertNotContains(response, reverse('users:login'))
        self.assertNotContains(response, 'staff-bar')
        self.assertNotContains(response, 'Вход для сотрудников')

    def test_password_change_errors_are_visible_and_password_is_unchanged(self):
        self.client.force_login(self.employee)
        cases = [
            ('Wrong-current-password', 'New-employee-password-82', 'New-employee-password-82', 'old_password'),
            ('Employee-test-password', 'New-employee-password-82', 'Different-password-93', 'new_password2'),
            ('Employee-test-password', '123', '123', 'new_password2'),
        ]
        for old, new, confirmation, invalid_field in cases:
            with self.subTest(field=invalid_field, new=new):
                response = self.client.post(reverse('users:password_change'), {
                    'old_password': old, 'new_password1': new, 'new_password2': confirmation,
                })
                self.assertEqual(response.status_code, 200)
                form = response.context['form']
                self.assertIn(invalid_field, form.errors)
                for errors in form.errors.values():
                    for error in errors:
                        self.assertContains(response, error)
                self.assertContains(response, 'aria-invalid="true"')
                self.assertContains(response, invalid_field + '_error')
                self.assertContains(response, 'autocomplete="current-password"')
                self.assertContains(response, 'autocomplete="new-password"')
                self.assertNotContains(response, 'value="' + new + '"')
                self.assertNotContains(response, 'cdn.jsdelivr.net')
                self.employee.refresh_from_db()
                self.assertTrue(self.employee.check_password('Employee-test-password'))

    def test_password_change_preserves_session_and_uses_new_password(self):
        self.client.force_login(self.employee)
        response = self.client.post(reverse('users:password_change'), {
            'old_password': 'Employee-test-password',
            'new_password1': 'New-employee-password-82',
            'new_password2': 'New-employee-password-82',
        })
        self.assertRedirects(response, reverse('users:password_change_done'))
        self.assertContains(self.client.get(reverse('users:password_change_done')), 'Вернуться в каталог')
        self.assertEqual(self.client.get(self.event.get_absolute_url()).status_code, 200)
        self.employee.refresh_from_db()
        self.assertTrue(self.employee.check_password('New-employee-password-82'))
        self.assertFalse(self.employee.check_password('Employee-test-password'))
        self.client.logout()
        self.assertTrue(self.client.login(username='employee', password='New-employee-password-82'))

    def test_logout_has_navigation_and_local_styles(self):
        self.client.force_login(self.employee)
        self.assertEqual(self.client.get(reverse('users:logout')).status_code, 405)
        response = self.client.post(reverse('users:logout'))
        for text in ('Войти снова', reverse('users:login'), 'users/staff.css'):
            self.assertContains(response, text)
        self.assertNotContains(response, 'cdn.jsdelivr.net')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_delete_requires_confirmation_and_has_cancel_link(self):
        url = reverse('events:event_delete', kwargs={'slug': self.event.slug})
        self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.employee)
        response = self.client.get(url)
        self.assertContains(response, 'Отмена')
        self.assertContains(response, 'href="' + self.event.get_absolute_url() + '"')
        self.assertNotContains(response, 'cdn.jsdelivr.net')
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())
        response = self.client.post(url)
        self.assertRedirects(response, reverse('events:index'))
        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())

    def test_password_pages_require_login(self):
        for name in ('users:password_change', 'users:password_change_done'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)

    def test_registration_and_email_password_reset_are_not_available(self):
        paths = (
            '/auth/signup/', '/auth/password_reset/', '/auth/password_reset/done/',
            '/auth/reset/MQ/example-token/', '/auth/reset/done/',
        )
        for path in paths:
            for method in ('get', 'post'):
                with self.subTest(path=path, method=method):
                    self.assertEqual(getattr(self.client, method)(path).status_code, 404)
