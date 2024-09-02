
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus

from events.models import Event, Category

User = get_user_model()


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = Category.objects.create(name='Тестовая категория',
                                slug='test-slug-category')
        cls.event = Event.objects.create(
            name='Тестовый заголовок',
            description='Тестовый текст',
            slug='test-slug',
            category=cls.category,
        )
 
    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index(self):
        url = reverse('events:index',)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_event_category(self):
        url = reverse('events:category_events', args=(self.category.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)    

    def test_about(self):
        url = reverse('events:about',)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create(self):
        url = reverse('events:event_create',)
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_event_detail(self):
        url = reverse('events:event_detail', args=(self.event.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
