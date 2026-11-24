"""Present editable catalog fields using the source PDF's typography and geometry."""
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def catalog_source():
    return json.loads(Path(__file__).with_name('catalog_source.json').read_text(encoding='utf-8'))


def _lines(value, block):
    style = {'400': 'regular', '700': 'bold', '900': 'black'}[block['weight']]
    widths = catalog_source()['metrics'][style]
    limit = block['width'] * 1000 / block['size']
    result = []
    for paragraph in value.splitlines():
        line, length = [], 0
        for word in paragraph.split():
            word_length = sum(widths.get(str(ord(c)), 500) for c in word)
            space = widths.get('32', 250) if line else 0
            if line and length + space + word_length > limit:
                result.append(' '.join(line))
                line, length, space = [], 0, 0
            line.append(word)
            length += space + word_length
        result.append(' '.join(line))
    return result


def prepare_program(event, number, total):
    source = catalog_source()
    page = str(event.catalog_page) if str(event.catalog_page) in source['layouts'] else '4'
    layout = source['layouts'][page]
    blocks = dict(layout['blocks'])
    # Pages without a dress-code note still support adding one in the editor.
    for name, block in source['layouts']['4']['blocks'].items():
        blocks.setdefault(name, block)
    runs = []
    labels = {
        'СЦЕНАРИЙ': 'scenario', 'ИНТЕРАКТИВЫ': 'interactives', 'ВЕДУЩИЙ': 'host',
        'АКТЁРЫ': 'actors', 'МУЗЫКА': 'music', 'РЕКВИЗИТ': 'props',
        'ФОРМАТ': 'program_format', 'ТАЙМИНГ': 'timing', 'ОБРАЗЫ': 'dress_code',
    }
    run_classes = {
        'АВТОРСКИЕ НОВОГОДНИЕ ПРОГРАММЫ': 'program-page-heading',
        'www.dievent.ru': 'program-footer-text',
    }
    for run in layout['labels']:
        field = labels.get(run['text'])
        if field and not getattr(event, field).strip():
            continue
        if run['text'] == 'ЧТО ВХОДИТ В КОНЦЕПЦИЮ' and not event.concept_features:
            continue
        runs.append({**run, 'css_class': run_classes.get(run['text'], '')})
    present_labels = {run['text'] for run in layout['labels']}
    for run in source['layouts']['4']['labels']:
        field = labels.get(run['text'])
        if field and run['text'] not in present_labels and getattr(event, field).strip():
            runs.append(run)
    for field, block in blocks.items():
        value = getattr(event, field, '')
        if not value.strip():
            continue
        for index, line in enumerate(_lines(value, block)):
            runs.append({**block, 'text': line, 'y': block['y'] + index * block['leading']})
    for key, value in (
        ('number', f'{number:02d}'), ('counter', f'{number:02d} / {total:02d}'),
        ('program', f'ПРОГРАММА  /  {number:02d}'),
    ):
        runs.append({
            **layout[key], 'text': value,
            'css_class': 'program-footer-text' if key == 'counter' else '',
        })
    # Mobile artwork has its own readable caption size, independent of the PDF.
    mobile_slogan = {
        **blocks['slogan'], 'x': 41, 'y': 430,
        'size': 21, 'leading': 25, 'width': 398,
    }
    return {
        'event': event, 'number': number, 'total': total, 'runs': runs,
        'image_number': {
            **layout['number'],
            'x': layout['number']['x'] - 42,
            'y': layout['number']['y'] - 84,
        },
        'image_slogan': [
            {
                **mobile_slogan, 'text': line,
                'y': mobile_slogan['y'] + index * mobile_slogan['leading'],
            }
            for index, line in enumerate(_lines(event.slogan, mobile_slogan))
            if event.slogan.strip()
        ],
        # These two source images contain baked-in captions below the red rule.
        # Cover that area before drawing the current editable slogan.
        'image_slogan_background': {'6': '#261d4b', '16': '#263546'}.get(page),
        'graphics_template': f'events/pdf/graphics-{int(page):02d}.html',
        'index_x': 65 if number <= 10 else 610,
        'index_name_x': 120 if number <= 10 else 665,
        'index_y': 220 + ((number - 1) if number <= 10 else (number - 11)) * 35,
        'index_hit_y': 200 + ((number - 1) if number <= 10 else (number - 11)) * 35,
    }
