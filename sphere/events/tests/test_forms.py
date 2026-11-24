import shutil
import tempfile
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from events.models import Event, Category

User = get_user_model()



class EventCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_root = tempfile.mkdtemp(prefix='mindsphere-test-')
        cls.addClassCleanup(shutil.rmtree, cls.media_root, ignore_errors=True)
        media_settings = override_settings(MEDIA_ROOT=cls.media_root)
        media_settings.enable()
        cls.addClassCleanup(media_settings.disable)
        cls.user = User.objects.create_user(username='HasNoName')
        cls.category = Category.objects.create(name='Тестовая категория',
                                slug='test-slug-category')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

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
        event = Event.objects.get()
        
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(event.name, 'Тестовое название')
        self.assertEqual(event.category.name, 'Тестовая категория')
        self.assertEqual(str(event.image), 'events/small.gif')
        self.assertEqual(Event.objects.count(), 1)
