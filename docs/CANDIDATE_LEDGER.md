# Candidate ledger

The ledger the [research constitution](RESEARCH_CONSTITUTION.md) §6 asks for.
One row per hypothesis that has been tested or is queued. Labels use the
constitution's vocabulary. Update the row whenever a stage moves it, citing the
report, and record the date. Ordered from most to least constrained.

Labels used:
* **Strongly disfavoured relative to tested reference profiles** — an estimated
  information gap under explicit plaintext/state assumptions; a priority screen,
  not a calibrated rejection or universal language bound.
* **Statistically rejected** — a calibrated test rejects the stated family on
  its stated domain.
* **Rejected within grid** — no tested setting fits; other settings remain
  open.
* **Search found no fit** — nothing compatible was found, but coverage or
  optimisation is not certified.
* **Compatible** / **Untested** — as stated.

Last updated 10 October 2026.

## Status summary (10 October 2026)

Read this first. Details and history are in the tables and dated notes below.

**Established structural observations** (replicated here; mostly known in the
literature, see the [review](reports/REVIEW_2026-09-24.md)):

* In Currier B, a word's n/l/r ending is associated with the next word's first
  glyph. The same rule transfers to hidden boundaries inside written words and
  holds on three transcriptions. A message-free generator also produces it.
* Vocabulary is associated with page, in Currier A and B. Conditioning on
  attributed hand reduces the B statistic by about 29%; A (one hand) keeps it.
* Voynich words are internally predictable, the final glyph strongly so, and
  common words are short.
* The tested v101 glyph variants (d, y, k, r, sh, p) behave as variants, not
  separate letters (row 11, the only calibrated statistical rejection here).

**Failures of specific tested constructions** (rows 1–10, 17–23). Each is a
bounded construction on stated sources and pages. None excludes a cipher family
or a language. In particular, row 23 constrains the tested Latin sources under
whole-word codes with two alternatives, not Latin word codes in general.

**Closed programme.** Whole-word forward modelling (rows 18–23) is closed.
Matching word shape, length and frequency/length structure is weak evidence on
its own: the models were trained on Voynich, and message-free generators can
reproduce such profiles. Reopen only if new evidence supplies a constraint the
programme did not have, such as a verified label reading or a text–image
association.

**Open hypotheses.** Rows 12–16 (grouped, word/mixed, drifting, syllabic,
context-dependent codes) and rows 24–26 (message-free mechanisms). The cipher
premise remains the working hypothesis; nothing here confirms or refutes it.

**Claims requiring external verification before use:**

* A 2026 report that the manuscript was rebound out of order in the fifteenth
  century (single outlet).
* A reported trigram-repetition contrast between Voynich and a medieval herbal
  (1.2% vs 23%), from another project's audit.
* Novelty of the v101 variant result, the hidden-boundary transfer and the
  pooling trap against 2025–2026 preprints not read in full.
* Whether 1,500–4,500-entry codebooks existed around 1420 (row 13 note).

**Next evidence** must link text to independently observed content:
the [image-annotation pilot](protocols/IMAGE_ANNOTATION_PILOT_2026-10-10.md)
and verified label–object alignment. See the
[exposure inventory](../results/exposure_inventory_2026-10-10/README.md)
before choosing any pages.

## Families with a verdict

| # | Candidate | Verdict | Binding evidence | Domain and limits | Next discriminating test |
|---|---|---|---|---|---|
| 1 | One glyph (raw or compound EVA) → one letter, one fixed table, spaces kept (simple substitution, homophone merging of ≤ 2 glyphs per letter) | **Strongly disfavoured relative to tested reference profiles** | Plaintext needs 1.0–2.4 bits more per 2–4-symbol window than Currier B can carry, under the fixed-decoder/reference assumptions ([capacity screen](../results/capacity_screen_2026-10-09/README.md)); also fails the cipher-family fingerprints (F1/F2) | Latin (Celsus, Pliny, Alfonsi), Italian (Dante), German (MHG); normalised spelling; plug-in estimates with a large margin | Low priority; formulaic and diplomatic plaintext sensitivity remains open |
| 2 | As 1, with two tables alternating by line, paragraph or page | **Strongly disfavoured relative to tested reference profiles** | Original one-bit allowance withdrawn; no-allowance comparison requires plaintext/state independence | Layout observability does not imply plaintext/state independence; see corrected screen | Measure conditional profiles for a stated layout mechanism |
| 3 | Manuscript searches of families 1–2 (9 Oct page pilot, line rotation, phase initialization) | **Search found no fit** | Better objective scores; competitive whole-word and line-shuffle controls; unstable mappings; no repeated readings ([pilot](../results/voynich_pilot_2026-10-09/README.md), [rotation](../results/line_rotation_2026-10-09/README.md), [phase](../results/phase_initialization_2026-10-09/README.md)) | Pages f26r, f31r, f39v | Retain as negative search evidence, not a family exclusion |
| 4 | Plain language or simple substitution, word spaces kept (F1) | **Rejected within grid** | Page-specific vocabulary, repetition, vocabulary shape ([cipher-family findings](reports/CIPHER_FAMILY_FINDINGS_2026-09-26.md)) | Tales, poetry and German texts, not page-topical herbals | Page-topical medieval herbal or recipe plaintext |
| 5 | Homophonic substitution of letters, word spaces kept (F2) | **Rejected within grid** | Far too many word types; no page-specific vocabulary | k = 40–90 symbols | Low priority |
| 6 | Nomenclator: homophonic letters plus up to 300 word codes (F3) | **Rejected within grid** | Vocabulary size, page-specific vocabulary | N ≤ 300 code words | Large-N word codes: row 12 |
| 7 | Scribal abbreviation, then substitution (F4) | **Rejected within grid** | Repetition, page-specific vocabulary | Fixed affix list | With a page-topical plaintext |
| 8 | Verbose letter/pair codes, fixed Naibbe tables, with or without nulls (F5, F7) | **Rejected within grid** | Almost no page-specific vocabulary (≤ 0.013 bits against Voynich's 0.2) | Fixed tables; Latin, Italian, German | Drifting tables: row 14 |
| 9 | Verbose syllable codes with a shared core (F6) | **Rejected within grid** | Page-specific vocabulary, repetition; its homophones would be trivially visible (AUC 0.9997) | h ≤ 8 variants | Low priority |
| 10 | Message-free assembly or copy-and-modify (R1, R2) | **Rejected within grid** | Assembly: no page-specific vocabulary; copy: vocabulary shape, line effects | Tested settings | Not a cipher hypothesis; kept as a control |
| 11 | v101 glyph variants are distinct letters | **Statistically rejected** (for d, y, k, r, sh, p) | No word-level information in variant choice, with calibrated power, including at the real minority rates ([V101](reports/V101_FINDINGS_2026-09-26.md), [follow-up](reports/V101_FOLLOWUP_FINDINGS_2026-09-26.md)) | f and cph not calibrated; v101 `A` is an o/a ambiguity | None |
| 18 | Whole-word disjoint codes with 1–3 IID alternatives; fixed global probabilities; preserved word units | **Search found no fit in forward-profile grid** (descriptive, not calibrated rejection) | [Stage 28](../results/word_homophones_2026-10-09/README.md): 504 panels, seven settings, recipes/Celsus/Pliny; no development draw jointly fits four frozen measures | Source/normalization dependent; abstract code IDs, no glyph morphology or historical key-size bound. No blind key search | Context-persistent choices at matched codebook size, or separately specified content-word lexicons |
| 19 | Two disjoint whole-word codes from independent first/middle/final glyph slots, with IID/page/word-page/25%-refresh choice | **Search found no fit in forward-profile grid** | [Stage 30](../results/structured_word_codes_2026-10-09/README.md): 96 cipher panels and 72 R2 controls; no joint development fit, selected models fail reserved B/IT/spacing/A profiles. Glyph entropy too high; fitted grammar covers 54.9% of reserved B tokens | One Italian culinary source; 1,484 types/2,968 codewords; random fixed dictionaries; bounded edge/interior lists, no exceptions. No key search or general slot-family exclusion | Model dependencies between codeword parts and test unseen-type coverage; do not increase persistence budget in this grammar |
| 20 | Two disjoint whole-word codes drawn from a dependent glyph-chain word-shape model (order-2 Witten–Bell, trained on 20,029 Currier B tokens), random assignment, IID/page/word-page/refresh choice | **Search found no fit in forward-profile grid** (descriptive) | [Stage 31](../results/word_shapes_2026-10-09/README.md): the shape model alone passes the frozen word-shape gate (glyph entropy, last-glyph dependence, length, 83% top-2,968 reserved coverage). The codebook fails all targets: codewords too long (6.1 vs 4.3–4.5 glyphs), glyph entropy 2.26 vs 1.98–2.07, coupling 0 vs 0.12–0.25. R2 (same training) also fails | One culinary source; random assignment only; 512 tokens per target; no key search. Not a rejection of word codes with frequency-ranked or context-conditioned assignment | Frequency-ranked assignment (short/probable codewords for common words) and context-conditioned variant choice for coupling, each under its own protocol |
| 21 | As row 20, but frequency-ranked assignment: commonest plaintext words get the most probable codewords | **Search found no fit in forward-profile grid** for B (descriptive) | [Stage 32](../results/ranked_assignment_2026-10-09/README.md): length 4.41 vs 4.34–4.52, frequency/length Spearman −0.19 vs −0.17 to −0.26; page association unchanged; coupling 0 vs 0.12–0.25 fails every B target. Marginal 4/12 neighbourhood hits on Currier A (one passage; weak A coupling) need replication | One culinary source; same strings as row 20; no key search | Context-conditioned variant choice for coupling (stage 33) |
| 22 | As row 21, with context-conditioned variant choice: pick the alternative whose final glyph suits the next codeword's initial (lift table from Voynich training folios); proportional, deterministic and refresh variants | **Search found no fit in forward-profile grid** (descriptive) | [Stage 33](../results/context_choice_2026-10-09/README.md): deterministic choice raises coupling to 0.09–0.10 (Voynich 0.12–0.25); closest development fit so far (max residual 1.16) but 0/12 on every target; refresh restores page association but loses coupling | Two alternatives; one culinary source; coupling partly built in by the training lift table; no tuning | Plaintext with stronger page topicality (medical sources) under the frozen mechanism: stage 34 |
| 23 | Row 22's frozen mechanism with Latin medical plaintext (Celsus, Pliny) instead of Italian recipes | **Search found no fit in forward-profile grid** (descriptive) | [Stage 34](../results/source_sensitivity_2026-10-09/README.md): whole-word codes inherit plaintext vocabulary richness; Latin gives cipher TTR 0.76–0.82 (Voynich 0.61–0.64) and codewords 5.2–5.3 glyphs; 0/12 on all targets for every source and rule. Celsus adds page association, Pliny removes it; coupling unchanged | Two Latin and one Italian source, two passages per split each; post hoc source choice is selection | Stem-plus-ending (morphological) codes, which could absorb inflection; not more parameters in rows 20–23 |
| 17 | Prefix-determined one/two-glyph codes, <=3 long-code prefixes or fixed width two; <=2 homophones; expansion 1.35–2; codes end at lines/drawings/unclean gaps | **No admissible original-page parser within this grid**; blind synthetic recovery still below gate | [Original pilot](../results/grouped_boundary_2026-10-09/README.md); [all-survivor repair](../results/parser_retention_2026-10-09/README.md) now selects the true parser 8/8, with 28.5–75.0% recovery and 0/8 at 90% | All 177 structural survivors searched; fixed 4,096 evaluations each. Key search incomplete. Original f26r infeasibility unchanged; no new manuscript key search | Do not prune on unigram concentration; prioritise larger units and justify boundary assumptions before another search |

## Open questions (not cipher families)

| Question | Status | Evidence |
|---|---|---|
| Do r/l/n endings encode different plaintext units? | Not decidable by context statistics on this corpus | [Coupling test v3](reports/COUPLING_TEST_V3_FINDINGS_2026-09-26.md) |
| What are the spaces? | Open. Coupling is about 6× stronger at doubtful spaces; transcriptions differ mainly there | [V101 follow-up](reports/V101_FOLLOWUP_FINDINGS_2026-09-26.md) |
| Do line and paragraph effects come from the cipher? | Every family needs an added layout convention to match them | [Cipher-family findings](reports/CIPHER_FAMILY_FINDINGS_2026-09-26.md) |

## Open families, in priority order

| # | Candidate | Why it is open | Next test |
|---|---|---|---|
| 12 | Grouped-glyph or verbose codes with inferred/unit spaces (U1/U2 + R2/R3 + S2/S3) | Larger units do not guarantee capacity. Parser pruning fixed on eight fixtures, but blind key recovery remains incomplete | [Unit study](../results/unit_association_2026-10-09/README.md): one-letter/one-token profiles fall short; this is not a ceiling on contextual or regrouped encoders |
| 13 | Word or mixed codes: bounded word-code list or whole-word codes (U3/U4) | **Open; overlap on one fingerprint for some sources.** Whole-word recipe/Alfonsi page-association ranges overlap Voynich; joint shape/layout mismatches remain. Top-frequency mixed50/200 profiles fall short | [Stage 27](../results/unit_association_2026-10-09/README.md); next align recurring labels and test independent referents; consider content-selected word lists, not just frequent function words |
| 14 | Verbose codes with section- or page-drifting tables or preferences (K2/Q7) | One route to page association; contextual coding and layout also remain possible | Extend the cipher-family benchmark with drift; check the page-specificity fingerprint |
| 15 | Syllable codes without a shared visible core | Heuristic syllable profiles reach 0.101 excess bits vs Voynich 0.115 in stage 27; a narrow reference gap, not exclusion of syllabic codes | Validate alternative segmentation and joint fingerprints; no additional letter-solver budget |
| 16 | State dependent on plaintext, or decoding using additional linguistic context | Open: the unconditional entropy comparison requires an independence assumption that these mechanisms need not satisfy | Specify state/context, sampling and a recoverable encoder before testing |
| 24 | Message-free: copy and modify (self-citation). Each word copies a recent word, usually from the lines above, with small glyph changes (Timm & Schinner; our R2) | Kept as a competitor, not only a control. R2 fails our joint screens as badly as the ciphers | Predicts similarity follows writing order and physical proximity; no dependence on illustration content beyond what position carries. Test: text–image association after position and layout controls |
| 25 | Message-free: table or slot generator (Rugg-style grille; our R1 assembly) with settings changed between sessions | Fixed settings give no page association (row 10); changing settings by session is untested | Predicts vocabulary shifts at session or bifolio boundaries, not at subject boundaries. Test: similarity by physical gathering versus by annotated image features |
| 26 | Message-free: human pseudo-writing with drifting habits (Gaskell & Bowern), possibly varying by illustration type | Not modelled here. A person imitating writing produces non-random structure | Hardest to separate: a writer could vary output with the kind of picture. The text–image protocol must include an image-associated pseudo-text comparison, not assume pseudo-text ignores pictures |

9 October correction and grouped-pilot update: the historical screen README retains its original wording
with a superseding correction notice. The expansion estimates are heuristics.
Hidden random state independent of plaintext is not automatically exempt from the
conditional bound; dependence and decoding context are the relevant distinctions.

9 October unit-study update: [stage 27](../results/unit_association_2026-10-09/README.md)
finds all-type within-section excess MI 0.115–0.124 bits across spacing arms,
0.092–0.105 after role conditioning. Word-shuffle controls are near zero.
These finite-sample fingerprints are not population information ceilings.
The [post hoc pooling audit](../results/unit_association_pooling_audit_2026-10-09/README.md)
demonstrates that first-occurrence ties at a top-200 cutoff can manufacture page
association (0.205 bits even for all-unique tokens). Rows 4–10 retain their
historical grid verdicts. The subsequent sufficient audit below closes the
specific ZL verdict concern. The unpooled new signal survives.

9 October stage-28 update: [historical pooling audit](../results/historical_pooling_audit_2026-10-09/README.md)
verifies all 456 original ZL configuration/window cells remain negative: 434
fail unchanged P1–P4; the remaining 22 fail recomputed P6 with new target
bootstrap SDs under both identity ties and no cap. All 132 required original
simulations replay their old P6 exactly. P5/P7–P9 shifts and IT/v101 full-grid
verdicts were not audited by this sufficient proof. Rows 4–10's ZL grid verdicts
therefore stand; no universal family exclusion is added.

Row 13 remains open beyond the narrow IID-alternative model in row 18. Original
page association replicates in IT2a, and a disjoint herbal/starred-text panel
retains the signal. Recipe genre cannot be identified from aggregate fits.
The [recurring-label preparation](../results/label_alignment_2026-10-09/README.md)
finds only four types crossing the declared split (minimum five); semantic
validation did not proceed, and exact coordinate candidates remain unverified.

9 October stage-29 update: [frequency/Currier A diagnostic](../results/frequency_currier_a_2026-10-09/README.md)
finds positive page association in both halves of matched herbal A/B panels,
across ZL/IT and spacing arms. Full ZL split A: 0.0783 bits section excess,
0.0485 role excess; B: 0.1349 and 0.0977. In B, types with ≥5 occurrences
contribute 0.1185 of 0.1349 section excess (87.9%). Frequency is not a semantic
classification; singleton zero is an estimator limitation, not absence of topic.
Rows 13/14 remain open and row 18's narrow IID result is unchanged. No generator
fit, statistical family rejection or reading was added. The
[next-model guardrails](guides/CONTEXT_CODEBOOK_GUARDRAILS.md) require explicit
slot capacity, state accounting, frozen-page comparison with R2 and independent
label alignment. Historical attestation of a large codebook around 1420 remains
unverified; do not assert it as a premise.

9 October stage-30 update: the fixed grammar supplies 14,336 distinct strings,
but capacity alone does not provide manuscript coverage or low glyph entropy.
Refresh selection transfers without retuning: reserved B role excess 0.088
versus 0.089 observed, while page excess is 0.193 versus 0.114 and glyph entropy
2.781 versus 2.072. R2 also fails the joint screen (glyph entropy 2.639).
Numbers are medians over declared draws, not a best key or a decipherment.
The 16/16 synthetic profile-calibration gate passed; all 168 panels replay and
49,152 synthetic words round-trip with known keys. Shuffle recurrence effects
do not establish a cipher-only property. Row 10's original verdict is unchanged;
this head-to-head adds a new narrow negative comparison, not a general rejection.

9 October stage-31 update: [scribe control, word shapes and codebooks](../results/word_shapes_2026-10-09/README.md).
Within Davis hands, 16-folio B keeps 0.096 of 0.135 bits section excess (71%),
below the 77–103% that twelve plaintext references keep on the same layout; part
of B's page association is between scribes. A (one hand) keeps all 0.078 bits.
A two-glyph-context chain reproduces word-internal predictability and the
nearly fixed final glyph that row 19's independent slots lacked (last-glyph
dependence 1.44 vs Voynich 1.54; slots 0.14), so row 19's "model dependencies"
test is done. The binding constraint moves to assignment (row 20). Voynich's common
words are short (type frequency/length Spearman −0.31, post hoc), and no
random-assignment codebook reproduces neighbour coupling. Rows 13/14 stay open;
no reading, family rejection or comparative support is added. Stolfi/Zattera
grammar baselines remain deferred (sources unreachable).

9 October stage-32 update: frequency-ranked assignment ([report](../results/ranked_assignment_2026-10-09/README.md))
removes the stage-31 length failure on the same strings and leaves page
association exactly unchanged. Coupling is the single binding B failure; the
marginal Currier A neighbourhood result is unreplicated and not a fit.

9 October stage-33 update: [context-conditioned choice](../results/context_choice_2026-10-09/README.md)
shows coupling can come from an encoder's choice between alternatives, but two
alternatives give only part of it. Persistence and context choice conflict.
The remaining B gap under the closest rule is page association, which the
recipe source supplies only partly.

9 October stage-34 update: [source sensitivity](../results/source_sensitivity_2026-10-09/README.md)
closes the whole-word line (rows 20–23) on these measures. Word shape, length
and frequency/length structure are solved; coupling is partly reproduced by
context choice. Vocabulary richness and page association now depend on the
plaintext. Inflected Latin coded word by word has too many types; the recipes
have too few, and lack page association. Row 13 remains open for other
representations (morphological or mixed codes). The marginal Currier A result
is reproduced only for the same recipe passage.

10 October correction ([boundary correction](../results/boundary_correction_2026-10-10/README.md)):
the coupling measure and context choice in rows 20–23 counted drawing-separated
words as neighbours, and secondary targets reused ciphertext encoded on the
reserved layout. Corrected reruns change no verdict. Row 22's closest
development fit is 1.37 (was 1.16) and its reserved B best 2.62 (was 2.33). The
stage-31 update's "71% within hands" is a reduction from conditioning on hand,
not an allocation of information between scribes. Directly corrected word/hand
association in B is 0.0995 bits, above twelve plaintext references (≤0.054).
Future positive claims for these rows need folios not used in stages 27–34.

10 October consolidation: status summary added above; rows 24–26 name specific
message-free mechanisms with the observation that would separate each from a
content-bearing text. "Any pseudo-writing" is no more testable than "any
cipher", so only stated mechanisms are listed. Wording corrections: stage 34
constrains the tested Latin sources and whole-word encodings only, and matching
word shape and length is weak evidence on its own, not zero. The
[exposure inventory](../results/exposure_inventory_2026-10-10/README.md) and the
frozen [image-pilot split](../results/image_annotation_pilot_2026-10-10/README.md)
are preparation; no annotation or text–image statistic exists yet.

10 October stage-35 update: [line-start indicator test](../results/line_indicator_2026-10-10/README.md).
On 1,374 Currier B lines the first glyph of a line does not predict later word
endings in that line (contrast −0.005 bits, interval −0.019 to 0.011). The
calibrated test detects a planted indicator altering 20% of endings in 16/20
trials. Rows 14 and 16 stay open, with a first-glyph line indicator acting on
a fifth or more of endings now bounded out. No key position predicts endings two
or more words away, so line-level table switching is unsupported for endings.
R2 is also null; this does not bear on cipher versus message-free text.

10 October stage-36 update: [label unit-size diagnostic](../results/label_units_2026-10-10/README.md).
778 single clean labels (622 types). Labels are not longer than same-frequency
words by the preset threshold (+0.12 glyphs, driven by labels absent from
running text) and split into common words at 63.7% against 60.0% for matched
words (p = 0.029, above the 0.0125 threshold). They do not recur in their own
page's text beyond a within-kind shuffle (10.9% vs 11.0%), nor as two adjacent
pieces (0.6% vs 0.6%; planted 2% effects detected 20/20). Rows 12, 13 and 15
stay open: labels do not discriminate word-sized from chunk-sized units. Exact
label matching is a poor route to cribs.
