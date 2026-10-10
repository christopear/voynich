# Image-annotation feasibility pilot: frozen split and blank templates

10 October 2026. **Preparation only. Nothing has been annotated and no
text–image association has been computed.**
[Protocol](../../docs/protocols/IMAGE_ANNOTATION_PILOT_2026-10-10.md),
[feature codebook](../../docs/guides/IMAGE_FEATURE_CODEBOOK.md),
[exposure inventory](../exposure_inventory_2026-10-10/README.md).

| Set | Bifolios | Pages | Use |
| --- | --- | --- | --- |
| Development | 11 (quires A–C) | 41 | Annotate now, two independent annotators |
| Confirmation X | 7 | 28 | Sealed until a text–image protocol is committed |
| Confirmation Y | 6 | 25 | Sealed; replication vault if X alone has adequate power |

All pages are herbal, Currier A, Davis hand 1, with at least 40 clean
paragraph tokens. The split is by bifolio, computed from metadata by
`python -m voynich.laboratory.image_annotation_packet` (`split.json`).

## What a human needs to do next

1. Obtain the Beinecke scans for the 41 development pages and record their
   source under `data/`. Prepare crops with the text masked.
2. Give two annotators the codebook and one template each
   (`development_template_A.csv`, `development_template_B.csv`). They work
   independently, without the transliteration or any statistic from this repo.
3. Return the two filled sheets. The pilot analysis (agreement, missingness,
   variation, power) is then run and the protocol's checkpoint applied.

From now on, do not run exploratory text statistics on pages in X or Y.
