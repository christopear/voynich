# Encoding units and page association — 9 October 2026

Prospective structural study, constitution §7; ledger rows 12–15, especially 13
(word/mixed) and 15 (syllable). No key fitting or plaintext claims. Source and
page inventories were inspected before registration; association outcomes were not.

## Domain and question

Each plaintext unit emits ONE apparent ciphertext word through a fixed,
page-independent channel. Compare letters, non-overlapping within-word pairs
(last singleton retained), heuristic syllables, words, and mixed top-50/top-200
word codes with other words emitted as individual letters. Mixed dictionaries
are fitted on a separate source partition. Unit type prefixes prevent collisions.
The existing `slot_cipher.syllabify` is a reversible segmentation heuristic,
not a validated medieval pronunciation model. Accent-folded a–z spelling retains
i/j and u/v; punctuation creates word boundaries. No abbreviation model.

For this aligned sampling scheme, C independent of page P given U implies
I(C;P) <= I(U;P) in the population. Bijections preserve empirical all-type MI
exactly. Permutation-subtracted MI and vocabulary-pooled MI do NOT inherit a
universal bound. These are finite-sample fingerprints, never language ceilings.
A letter cipher keeping entire plaintext words as output tokens is outside the
one-letter/one-apparent-word arm and can preserve word association.

## Manuscript and sampling

ZL3b P0 Currier B only. Select first eight herbal (I=H) and eight biological
(I=B) pages in transcription order, at most one side per folio. Eligibility:
at least 64 clean tokens in EACH of two spacing arms. Split arm accepts both
ordinary and doubtful spaces as boundaries; join arm merges clean neighbours
only across doubtful spaces. Never cross drawings, lines or unclean tokens.
Take first 64 tokens per page. Retain original line-initial, line-final and
paragraph-first-line flags, without pretending removed tokens were adjacent.
Record exact loci, original token indices, words and metadata in the evidence.
The 16 pages are previously exposed manuscript data, not a pristine holdout.
Use raw word identities, not inferred semantic topics. Other transcriptions
are deferred; these spacing arms do not substitute for that sensitivity.

## Reference panel

Celsus De Medicina books 1–8, Pliny Naturalis Historia books 20–27 (ancient
medical/herbal Latin, modern scholarly editions); anonymous Il libro della
cucina del sec. XIV, Zambrini's 1863 edition (Italian culinary recipes, NOT
medical); existing Alfonsi tales and Dante poetry as literary contrasts.
Pinned raw files, hashes, licences and extraction under data/unit_association_sources.
Exclude medical headings/notes/foreign gaps and recipe introduction, chapter
headings, centred subheadings, printed page numbers and footnote markers.
Natural chapter/recipe-heading groups for the first three; artificial contiguous
256-word blocks for literary controls. Neither printed chapters nor artificial
blocks are claimed to reproduce a medieval manuscript's page breaks.

Eligible source units have >=64 normalized words. First max(1,floor(N/5))
eligible units train mixed dictionaries; never use them in measurement.
For each seed 7, 19, 31, sample 16 distinct remaining units, and sample a
contiguous 64-output-unit window from each representation. No wrapping,
replacement or concatenation between chapters. One sampled chapter per target
page; chapter assignment is identical across representations for a seed, but
spans differ. Assign its units to the split-arm manuscript's 64 layout slots.
Matching output token counts deliberately samples different amounts of
plaintext at different unit sizes. Record every selected chapter and offset.
Reference sections/layout labels are assigned slots, not historical source
sections. Seeds are passage/layout sensitivity, not independent corpora.

## Measurements and controls

For all types and top-200 types plus OTHER (tie by first occurrence), report
raw I(token;page), I(token;page | section), and I(token;page | section, roles).
For each, subtract the mean of 199 whole-token permutations within its
conditioning strata. Report null SD and Monte Carlo SE of that mean; negative
excess values are retained. This controls finite occupancy and preserved margins,
NOT arbitrary temporal dependence. It is a descriptive exchangeability null,
not a calibrated family-rejection p-value or confidence interval for population MI.

Primary comparison: all-type within-section excess MI. Sensitivities: roles,
top-200 pooling, doubtful-space joining, section-separated panels (8 pages each),
and 199 permutations of 8-token consecutive blocks within section. The block
null retains short-range repeats but does not preserve line/paragraph roles;
report it separately. Vocabulary size/type-token ratio, hapax-type share,
top-ten-token share and adjacent-repeat rate are joint descriptive fingerprints.
No threshold is tuned to label a candidate successful.

Manuscript controls, seeds 7/19/31: (a) whole-token shuffle within section and
roles, preserving vocabulary; (b) shuffle component EVA glyphs within each page,
retaining token lengths and page glyph counts. Both use the same measurement
procedure. These are controls of association/word formation, not solver searches.

Estimator checks before manuscript measurement: exact bijection invariance,
deterministic coarsening cannot increase raw aligned empirical MI, synthetic
page-dependent mapping can create association absent from source units, 50
uniform IID panels and 10 planted page-vocabulary panels with the same 16×64
layout. Report their excess distributions; do not silently recalibrate based on
manuscript outcomes. Unit and extraction tests must pass before running.

## Budget, decisions and limits

5 sources × 6 representations × 3 seeds = 90 reference panels, two manuscript
spacing panels and six control panels. 199 permutations per statistic; no
adaptive reruns. Calibration: 50 null + 10 planted panels, primary statistic only.
No new solver training or source selection from results. Report source-wise
ranges, never average away genre effects or call passage seeds independent trials.

A reference overlap keeps an arm open on this fingerprint only; it does not
establish a recoverable cipher, sufficient capacity or a shared generator.
Consistent shortfall is a conditional reference-profile gap, not universal
exclusion. If pooling, null choice, spacing or source choice changes priorities,
report that instability rather than reject a family. If estimator calibration
fails (IID mean excess >0.02 bits in absolute value, or planted mean <=0.1), stop
before manuscript measurement. Register protocol and producing code before run.
Next steps must address remaining fingerprints and independently checkable
predictions; this study cannot identify words or prove a codebook.
