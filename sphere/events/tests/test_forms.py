import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from events.models import Event, Category

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class EventCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.category = Category.objects.create(name='Тестовая категория',
                                slug='test-slug-category')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @override_settings(MEDIA_ROOT=(TEMP_MEDIA_ROOT + '/media'))
    def test_create_event(self):
        """Валидная форма создает запись в Event."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'name': 'Тестовое название',
            'slug': 'Test-slug-form',
            'description': 'Тестовая запись через форму',
            'category': self.category.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('events:event_create'), data=form_data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        event = Event.objects.last()
        self.assertEqual(event.name, 'Тестовое название')
        self.assertEqual(event.category, self.category)
        self.assertEqual(str(event.image), 'events/small.gif')
        self.assertEqual(Event.objects.count(), 1)
