"""Position programs within the published catalog."""
from django.db import transaction

from .models import Event


def catalog_position(event):
    if not event.pk or not event.is_published:
        return None
    ids = list(Event.objects.filter(is_published=True).values_list('pk', flat=True))
    return ids.index(event.pk) + 1 if event.pk in ids else None


@transaction.atomic
def save_at_position(event):
    # Lock the current list and renumber it as one transaction.
    published = list(Event.objects.select_for_update().filter(is_published=True))
    others = [item for item in published if item.pk != event.pk]
    if event.is_published:
        index = min(max(event.sort_order - 1, 0), len(others))
        event.sort_order = index + 1
        others.insert(index, event)
    event.save()
    changed = []
    for position, item in enumerate(others, 1):
        if item.sort_order != position:
            item.sort_order = position
            changed.append(item)
    if changed:
        Event.objects.bulk_update(changed, ['sort_order'])
    return event
