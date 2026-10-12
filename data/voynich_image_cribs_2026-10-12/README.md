# Voynich page images: plant descriptions and crib words (12 October 2026)

Separate exploratory exercise, requested by the user. It is not a stage of the
numbered research programme.

* `plant_cribs.json`: one entry per scan image (front cover, inside cover,
  folios 1r–116v, back flyleaf, edges, spine, back cover). 213 entries in
  all. Folios 12, 59–64, 74, 91–92, 97–98 and 109–110 are absent from the
  Yale scans. A fold-out scanned as one image is one entry (`69v+70r`,
  `71v+72r`); a side scanned as two images is split (`70v_part1`,
  `70v_part2`, `72v_part1`, `72v_part2`). Binding photographs have `page: null`.
* `build_cribs.py`: the per-page observations; it writes the JSON
  (`python3 build_cribs.py plant_cribs.json`).

Each entry has these fields:

* `page`: the scan image order from 1r = 1, so 2v = 4.
* `folio`: the folio number written on the scan.
* `description`: what is drawn, in English.
* `candidates_en`: possible plants, in English.
* `confidence`: how sure the identification is.
* `crib`: crib words from the three languages combined into one list.
* `crib_by_language`: the same crib words split into `la` (medieval
  Latin herbal and apothecary names), `it` (Italian vernacular) and `de`
  (Middle and Early New High German).

**Source:** Beinecke MS 408 scans (Yale image IDs 1006074–1006279), supplied by
the user as six PDFs. The PDFs are not committed.

**Method and limits:** an AI looked at each scan. No published Voynich
identifications or decipherment literature were consulted. Most drawings are
stylised, so the identifications are guesses: 9 high, 47 medium, 120 low,
37 not applicable. The 8 high-confidence entries in 36v–79r are zodiac
wheels whose sign is drawn and whose centre carries a Latin-script month
name in a different hand (read here as `mars`, `abril`, `augst`, `octebre`,
`novebre`; others too small or faint to read). Non-plant pages (zodiac,
star and cosmological diagrams, bathing scenes, text-only pages) get
cribs for what they appear to show: months, signs, stars, winds,
elements, baths, water and pipes. The pharmaceutical pages (88r–102v) get
jar, root and remedy vocabulary as well as plant names. The star-marked
text pages (103r–116r) get recipe vocabulary. Folio 116v carries a few
lines in the Latin alphabet in another hand, with words separated by
crosses; the reading in its entry is tentative. Crib lists name several candidate plants on purpose.
Period spellings vary a lot; the forms given are common ones, not the only
ones. Nothing here is a decipherment or a verified label.
