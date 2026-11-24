from types import SimpleNamespace

from django.contrib.admin import AdminSite
from django.test import SimpleTestCase, override_settings

from events.admin import EventAdmin
from events.models import Event


class EventAdminThumbnailTests(SimpleTestCase):
    def setUp(self):
        self.model_admin = EventAdmin(Event, AdminSite())

    @override_settings(MEDIA_URL='/media/')
    def test_thumbnail_with_image(self):
        event = Event(image='events/example.png')

        self.assertHTMLEqual(
            self.model_admin.image_thumbnail(event),
            '<img src="/media/events/example.png" width="50" height="50" />',
        )

    def test_thumbnail_without_image(self):
        self.assertEqual(self.model_admin.image_thumbnail(Event()), '-')

    def test_thumbnail_escapes_storage_url(self):
        event = SimpleNamespace(
            image=SimpleNamespace(url='/media/image.png" onerror="alert(1)'),
        )

        self.assertEqual(
            self.model_admin.image_thumbnail(event),
            '<img src="/media/image.png&quot; onerror=&quot;alert(1)" '
            'width="50" height="50" />',
        )
