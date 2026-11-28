from types import SimpleNamespace

from pytest_django.asserts import assertHTMLEqual

from events.models import Event


def test_thumbnail_with_image(model_admin):
    event = Event(image='events/example.png')
    assertHTMLEqual(model_admin.image_thumbnail(event), '<img src="/media/events/example.png" width="50" height="50" />')


def test_thumbnail_without_image(model_admin):
    assert model_admin.image_thumbnail(Event()) == '-'


def test_thumbnail_escapes_storage_url(model_admin):
    event = SimpleNamespace(image=SimpleNamespace(url='/media/image.png" onerror="alert(1)'))
    assert model_admin.image_thumbnail(event) == '<img src="/media/image.png&quot; onerror=&quot;alert(1)" width="50" height="50" />'
