"""Load the supplied DI EVENT catalog without deleting private descriptions or files."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from pytils.translit import slugify

from events.catalog import catalog_source
from events.models import Event


class Command(BaseCommand):
    help = 'Загрузить все 21 программу DI EVENT; --replace убирает остальные из публичного каталога.'

    def add_arguments(self, parser):
        parser.add_argument('--replace', action='store_true')

    def handle(self, *args, **options):
        rows = catalog_source()['programs']
        if len(rows) != 21 or {r['sort_order'] for r in rows} != set(range(1, 22)):
            raise CommandError('Неверный состав исходного каталога.')
        aliases = {1: 'Рок-н-ролльная вечеринка', 2: 'Гэтсби'}
        art_root = Path(__file__).resolve().parents[2] / 'static/events/catalog/art'
        for row in rows:
            src = art_root / f"{row['sort_order']:02d}.png"
            dst = Path(settings.MEDIA_ROOT) / row['image']
            if not src.is_file():
                raise CommandError(f'Нет иллюстрации: {src.name}')
            content = src.read_bytes()
            if dst.exists() and dst.read_bytes() != content:
                raise CommandError(f'Файл уже существует с другим содержимым: {dst.name}')
        with transaction.atomic():
            active_ids = []
            for row in rows:
                values = row.copy()
                order = row['sort_order']
                event = Event.objects.filter(catalog_page=row['catalog_page']).first()
                if event is None:
                    event = Event.objects.filter(name=aliases.get(order, row['name'])).first()
                if event is None:
                    event = Event.objects.create(
                        name=row['name'], slug=slugify(row['name']), description='',
                    )
                src = art_root / f'{order:02d}.png'
                dst = Path(settings.MEDIA_ROOT) / row['image']
                if not dst.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    with dst.open('xb') as output:
                        output.write(src.read_bytes())
                # Preserve uploaded originals: the cleanup signal must not delete them.
                Event.objects.filter(pk=event.pk).update(**values, is_published=True)
                active_ids.append(event.pk)
            archived = 0
            if options['replace']:
                archived = Event.objects.exclude(pk__in=active_ids).filter(is_published=True).update(is_published=False)
        self.stdout.write(self.style.SUCCESS(
            f'Каталог: {len(active_ids)} программ. Убрано из публичного списка: {archived}. '
            'Пользователи, внутренние описания и прежние файлы сохранены.'
        ))
