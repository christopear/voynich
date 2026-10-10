# Image-annotation feasibility pilot (herbal illustrations)

Committed before any annotation. This is a **feasibility pilot**, not a
text–image test. It asks whether a small set of visible plant features can be
recorded reproducibly, and whether they vary enough to support a later bounded
test. **No text–image association is computed in this pilot, on any page.**
Ledger: new open question "text–image content association"; rows 24–26
(message-free mechanisms) are its competitors.

## Why this, and why now

The whole-word modelling programme (ledger rows 18–23) is closed. Matching
Voynich's aggregate statistics cannot distinguish a cipher from structured
pseudo-text: several generators without a message can pass joint profiles, and
our shape and coupling models were trained on Voynich itself. The next evidence
has to connect text to something observed independently of the text. Herbal
illustrations are the largest such resource.

## Data exposure and the frozen split

The [exposure inventory](../../results/exposure_inventory_2026-10-10/README.md)
shows no herbal page is untouched. Of 129 herbal pages, 94 have only pooled
exposure (tier ≤ 2), and 79 of those are Currier A in Davis hand 1. A
bifolio-separated low-exposure set exists for A/hand 1 only, not for Currier B.

Split rule (computed from metadata only by
`voynich.laboratory.image_annotation_packet`, stored in
`results/image_annotation_pilot_2026-10-10/split.json`):

* Eligible: herbal (`$I=H`), Currier A, hand 1, at least 40 clean paragraph
  tokens. One page (f36v) is excluded for low text.
* Group: bifolio = (`$Q`, `$B`).
* **Development**: every eligible page on a bifolio where any herbal page has
  been in a targeted panel (tier ≥ 3). 41 pages, 11 bifolios, quires A–C.
* **Confirmation**: the remaining 13 bifolios in manuscript order, alternating
  into X (28 pages, 7 bifolios) and Y (25 pages, 6 bifolios).

Restricting to one attributed hand and one Currier language removes those two
confounds by design. It also limits scope: any later result is about herbal A.
Development pages are the front three quires and confirmation pages the later
ones, so position in the book differs between them. A later test must model
physical position, not assume the sets are exchangeable. No page in X or Y may
be used for exploratory text statistics from now on.

X versus Y: if the pilot's power check (below) shows X alone is adequate, Y is
kept sealed as a replication vault. Otherwise X∪Y is the confirmation set and
no vault exists; say so plainly in that case.

## Features

Defined in the [codebook](../guides/IMAGE_FEATURE_CODEBOOK.md). Six content
features (leaf division, leaf arrangement, stem branching, root form, flower
presence, flower form) and four covariates (number of plants on the page, text
position relative to the plant, blue pigment, red pigment). Every feature has
an explicit "not visible / cannot decide" code. No botanical identification, no
species names, no medicinal interpretation.

## Annotation procedure (development pages only)

1. Images: Beinecke Library public-domain scans of MS 408. Record source URL,
   access date and image identifiers under `data/` before annotation. Prepare
   crops with the text regions masked, by someone or something other than the
   annotators.
2. Two annotators independently fill
   `development_template_A.csv` and `development_template_B.csv` for all 41
   development pages. They must not have the transliteration, any statistic
   from this repository, or each other's sheet. Annotators record who they are
   and whether they have prior familiarity with Voynich research.
3. An AI model may annotate as a third rater to speed later scaling. It has
   been exposed to Voynich material and to this repository's analyses, so it is
   **not** an independent blind observer. Its sheet is reported separately and
   never substitutes for a human rater in the agreement gate.
4. Annotators do not see confirmation pages X or Y during the pilot.

## Measurements and gate

Per content feature, on development pages:

* Agreement: Cohen's kappa between the two human annotators (weighted for
  ordered features), with a bootstrap interval over pages.
* Missingness: share of pages coded "not visible / cannot decide" by either.
* Variation: share of the commonest category; number of quires in which the
  feature takes at least two values.

A feature is **usable** if kappa ≥ 0.60, missingness ≤ 20%, the commonest
category covers ≤ 80% of pages, and it varies within at least two of the three
development quires.

Power check (simulation on development annotations and metadata only, no
manuscript text): for each usable feature, simulate a planted association of
stated size between a page-level text score and the feature, at the
confirmation sample sizes (28 for X; 53 for X∪Y), grouped by bifolio. Report
the smallest effect detectable with 80% power under a bifolio-level permutation
test at α = 0.05, with multiplicity over the usable features.

**Checkpoint.** Proceed to a text–image protocol only if at least three content
features are usable and the detectable effect at the available sample is one a
content relationship could plausibly produce (to be argued in the pilot report
before any confirmation text is touched). Otherwise stop this route. Redirect
to verified label–object alignments, and record that herbal A cannot support
the test at this sample size. Do not loosen the thresholds after seeing
agreement.

## What a later protocol must contain (not part of this pilot)

One primary question: does text predict independently annotated illustration
features on confirmation pages, beyond what layout, physical position and book
structure predict? It compares three stated explanations: production habits;
content association; and image-associated pseudo-text (non-semantic generation
that also varies with illustration category). The method is calibrated on a
known illustrated text and on synthetic alternatives before confirmation results
are opened. A positive result would support a text–image content
relationship; it would not establish a cipher or a translation. A negative
result would limit that relationship only: medicinal text need not describe
visible plant anatomy.

## Outputs

Pilot report with agreement, missingness, variation and power tables, the
annotators' sheets, image provenance, and the checkpoint decision. Update the
ledger. Historical results unchanged.
