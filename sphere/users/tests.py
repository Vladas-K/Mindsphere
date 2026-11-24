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
        for url in (reverse('events:index'), reverse('events:about')):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertNotContains(response, reverse('users:login'))
                self.assertNotContains(response, 'staff-bar')
                self.assertNotContains(response, 'Вход для сотрудников')
