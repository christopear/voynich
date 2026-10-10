# Data exposure inventory

10 October 2026. Descriptive bookkeeping, not an analysis: which manuscript
pages earlier work used, and in what role. Produced by
`python -m voynich.laboratory.exposure_inventory`. It reads page metadata,
stored panels and stage documentation; it computes no text statistic beyond
token counts.

## Tiers

| Tier | Meaning |
| --- | --- |
| 1 | Whole-manuscript descriptive statistics only |
| 2 | Pooled statistics or model training within a language/section pool |
| 3 | Targeted development, fitting or annotation panel |
| 4 | Targeted evaluation, reserved or solver-target panel |

Each rule in `inventory.json` names its stages and whether its page set comes
from stored panels or code (`code`) or from stage reports (`documentation`).
The Currier B pool rule is documentation-based: stages 9–18 and 24–25 describe
Currier B pools and folds, and page roles inside those folds are not separated.

## What it shows

* **No page is untouched.** All paragraph text was read for boundary and
  transcription statistics (stages 6–8, 12, 19–23).
* Of 129 herbal pages: 94 have at most pooled exposure (tier ≤ 2), 14 were in
  targeted development panels and 19 in targeted evaluation or solver panels.
  Two have no paragraph text or no Currier label.
* **Currier A, hand 1:** 79 of 95 herbal pages have only pooled exposure
  (stages 1–3 and 12 used the whole herbal A hand-1 pool). Thirteen whole
  bifolios hold no targeted page.
* **Currier B herbal:** 15 of 32 pages have only pooled exposure, and nearly all
  share a bifolio with a targeted page. They also trained the stage 31–34 shape
  model and lift table. A bifolio-separated low-exposure B set does not exist.
* **No analysis in this repository has used variables taken from the
  illustrations.** The label packet holds coordinate candidates for zodiac
  labels only. For a text–image study the relevant exposure is to text–image
  associations, and there has been none.

## Limits

Tiers describe this repository's work, not the wider literature: every page
has been studied by others. "Low exposure" means no targeted panel here, not
untouched. Pages are grouped into bifolios by the ZL `$Q` and `$B` variables;
those reflect the current binding, which may not be the original order.

Files: `inventory.json` (rules, every page, herbal bifolios), `herbal_pages.csv`.
