# DI EVENT catalog artwork

`art/01.png`–`21.png` are the original visible illustrations from the supplied
DI EVENT catalog. Programs 08, 11 and 17 use the visible DIReviewArtwork objects.
The files are unchanged. Fonts extracted from that catalog are now in
`../fonts/`; their Unicode maps support Cyrillic and Latin browser text.

`sphere/events/catalog_source.json` contains the public import records and
original-artwork palette metadata. Import with `load_catalog --replace`
only when intentionally restoring public fields; normal edits belong in forms
or Django Admin. The command restores the source catalog; it does not generate PDF files.

The responsive website uses shared HTML components and `catalog-responsive.css`.
There are no separate SVG page templates or dedicated print styles.
