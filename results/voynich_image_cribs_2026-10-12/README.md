# Voynich page images: plant descriptions and crib words (12 October 2026)

Separate exploratory exercise, requested by the user. It is not a stage of the
numbered research programme.

* `plant_cribs.json`: one entry per scanned page (front cover, inside cover,
  folios 1r–36r; folio 12 is absent from the scans). 71 entries in all.
* `build_cribs.py`: the per-page observations; it writes the JSON
  (`python3 build_cribs.py plant_cribs.json`).

Each entry has these fields:

* `page`: the scan order from 1r = 1, so 2v = 4.
* `folio`: the folio number written on the scan.
* `description`: what is drawn, in English.
* `candidates_en`: possible plants, in English.
* `confidence`: how sure the identification is.
* `crib`: crib words from the three languages combined into one list.
* `crib_by_language`: the same crib words split into `la` (medieval
  Latin herbal and apothecary names), `it` (Italian vernacular) and `de`
  (Middle and Early New High German).

**Source:** Beinecke MS 408 scans (Yale image IDs 1006074–1006144), supplied by
the user as two PDFs. The PDFs are not committed.

**Method and limits:** an AI looked at each scan. No published Voynich
identifications or decipherment literature were consulted. Most drawings are
stylised, so the identifications are guesses: 1 high, 19 medium, 48 low,
3 not applicable. Crib lists name several candidate plants on purpose.
Period spellings vary a lot; the forms given are common ones, not the only
ones. Nothing here is a decipherment or a verified label.
