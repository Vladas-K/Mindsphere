
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from http import HTTPStatus

from events.models import Event, Category

User = get_user_model()


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        category = Category.objects.create(name='Тестовая категория',
                                slug='test-slug-category')
        Event.objects.create(
            name='Тестовый заголовок',
            description='Тестовый текст',
            slug='test-slug',
            category=category,
        )
 
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)


    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about(self):
        response = self.guest_client.get('/about/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_event_detail(self):
        response = self.guest_client.get('/events/test-slug/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_event_category(self):
        response = self.guest_client.get('/category/test-slug-category/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
