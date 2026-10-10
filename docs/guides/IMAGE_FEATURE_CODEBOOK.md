# Image feature codebook for herbal pages (pilot version 1, 10 October 2026)

For the [image-annotation feasibility pilot](../protocols/IMAGE_ANNOTATION_PILOT_2026-10-10.md).
Code what is **drawn**, not what the plant might be. Do not identify species,
do not consult herbals, and do not use the text. If you cannot decide between
two codes after a careful look, use `9`. Do not guess.

Fill one row per page. Use the codes exactly. Put anything unusual in `notes`.

## Content features

| Column | Codes |
| --- | --- |
| `leaf_division` | `1` margins smooth or only slightly wavy; `2` toothed, scalloped or shallowly lobed; `3` deeply cut, lobed more than halfway, or made of separate leaflets; `9` no leaves drawn or cannot decide |
| `leaf_arrangement` | `1` leaves mainly from the base, at or near ground level; `2` leaves mainly along the stem, one per point; `3` leaves along the stem in pairs or rings; `9` cannot decide |
| `stem_branching` | `1` a single unbranched stem, or none; `2` the stem divides into two or more leaf- or flower-bearing branches; `9` cannot decide |
| `root_form` | `1` one main thick root; `2` many thin roots of similar size; `3` a swollen, bulb-like or tuber-like body; `4` drawn as an object, animal, face or other clearly non-plant shape; `9` no root drawn or cannot decide |
| `flower_presence` | `0` no flower, bud, fruit or seed head drawn; `1` at least one drawn; `9` cannot decide |
| `flower_form` | `1` single at a stem tip; `2` several separate ones; `3` a dense cluster or head; `8` not applicable (`flower_presence` is `0`); `9` cannot decide |

`leaf_division` is ordered (1 < 2 < 3). The others are unordered categories.

If the page shows more than one plant, code the largest. Record the count in
`plants_on_page`.

## Covariates (not content; recorded so they can be controlled for)

| Column | Codes |
| --- | --- |
| `plants_on_page` | `1` one plant; `2` two or more |
| `text_position` | `1` text only above the plant; `2` text beside or wrapped around the plant; `3` text in separate blocks above and below or on both sides; `9` cannot decide |
| `blue_pigment` | `0` none visible; `1` present |
| `red_pigment` | `0` none visible; `1` present |

Pigment may have been added later by another hand. It is a covariate, not
evidence about content.

## Other columns

* `annotator`: your letter (already filled).
* `image_source`: the image identifier you were given.
* `confidence`: `1` low, `2` medium, `3` high, for the page as a whole.
* `notes`: free text. Do not write plant names or guesses about meaning.

## Before you start

State in your first row's `notes` whether you have studied the Voynich
manuscript before, and whether you have seen this page's transliteration or any
analysis of its text. Prior familiarity does not disqualify you; it is recorded.
