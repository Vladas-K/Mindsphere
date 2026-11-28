"""Prepare artwork colours for the shared HTML catalog."""
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def catalog_source():
    return json.loads(Path(__file__).with_name('catalog_source.json').read_text(encoding='utf-8'))


# Bottom edge colours extend the original artwork when a caption grows.
ART_BACKGROUNDS = {
    '4': '#2d2725',
    '5': '#362a22',
    '6': '#261d4b',
    '7': '#401f29',
    '8': '#f8e4c6',
    '9': '#2f1621',
    '10': '#151414',
    '11': '#dcd3c3',
    '12': '#211b1d',
    '13': '#f6d0a6',
    '14': '#efe5d3',
    '15': '#deeaed',
    '16': '#263546',
    '17': '#98b6c7',
    '18': '#fae7cd',
    '19': '#252732',
    '20': '#382640',
    '21': '#747961',
    '22': '#1a2535',
    '23': '#0e1d16',
    '24': '#1f1628',
}


ART_RULES = {
    '4': '#de2430',
    '5': '#af7a2b',
    '6': '#e44757',
    '7': '#c77d5c',
    '8': '#b17736',
    '9': '#ca9a4c',
    '10': '#dd1f2e',
    '11': '#a6372f',
    '12': '#e12730',
    '13': '#d52a37',
    '14': '#bd3434',
    '15': '#cf3035',
    '16': '#e0333d',
    '17': '#db262e',
    '18': '#d33a2d',
    '19': '#c0282f',
    '20': '#d24155',
    '21': '#bf403b',
    '22': '#e1293f',
    '23': '#47b27a',
    '24': '#e0944c',
}



def prepare_program(event, number, total):
    """Only original illustrations inherit their palette and baked-caption masks."""
    page = str(event.catalog_page)
    artwork = catalog_source()['artwork'].get(page)
    original_art = bool(artwork and event.image and event.image.name == artwork['image'])
    return {
        'event': event, 'number': number, 'total': total,
        'art_ink': artwork['number_ink'] if original_art else '#ffffff',
        'slogan_ink': artwork['slogan_ink'] if original_art else '#ffffff',
        'art_rule': ART_RULES.get(page, '#b43c46'),
        'art_background': ART_BACKGROUNDS[page] if original_art else '#263546',
        'original_art': original_art,
        'cassette_label': original_art and page == '6',
        'image_slogan_background': {'6': '#261d4b', '16': '#263546'}.get(page) if original_art else None,
    }
