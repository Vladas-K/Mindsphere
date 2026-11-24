# DI EVENT catalog assets

Source: user-supplied `DI_EVENT_Каталог.pdf`, 25 landscape pages (1200 × 675),
including 21 programs. These are the original visible illustrations and embedded
Lato fonts, not generated replacements. The font character maps were restored
from the PDF's ToUnicode tables for normal Cyrillic/Latin browser text.

- `art/01.png`–`21.png`: illustrations actually referenced by the final page
  content stream. Programs 08, 11 and 17 use the replacement DIReviewArtwork
  objects; larger unused image objects in the PDF are not the visible artwork.
- `fonts/`: embedded regular, bold and black font outlines.
- `../../../catalog_source.json`: public field values, font widths and layout
  coordinates from the source. This file is an explicit import source, not a
  replacement for the editable database records.
- `sphere/templates/events/pdf/`: original vector graphics (without baked text)
  and static text of the cover, introduction, contents heading and contact page.

After applying migrations, load the source with:

```bash
# From the repository root. This resets the public fields to their source values.
venv/bin/python sphere/manage.py load_pdf_catalog --replace
```

The command copies illustrations to MEDIA_ROOT, creates/updates the 21 records,
keeps existing private descriptions, users and files, and unpublishes other
programs with `--replace`. It never runs automatically during a migration or
server startup. Edit content through the normal application forms or Django Admin.
Do not change the source JSON to make routine edits to a live program.

The page uses editable SVG text and vectors, not screenshots of PDF pages or a
PDF iframe. Guests see only public fields; details and editor routes require login.
