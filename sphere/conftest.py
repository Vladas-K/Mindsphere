import pytest
from events.models import Event, Category


@pytest.fixture
def category():
    category = Category.objects.create(
        name='example category', 
        slug='example-slug'
    )
    return category


@pytest.fixture
def event(category):
    event = Event.objects.create(
        name='example event', 
        description = 'example-description', 
        slug='example-slug',
        category=category
    )
    return event