# Operation families and initial research priorities

26 September 2026. Companion to [the constitution](RESEARCH_CONSTITUTION.md).
Working premise: manually executable cipher of Latin or Italian, initially
tested against Currier B. Evidence baseline: `5463771` on
`claude/gifted-wright-ctbvn0`.

## Reading the scores

These are subjective investigation priorities, not estimated probabilities or
historical prevalence. They combine manual plausibility, relevance to the
project's findings, and how much a test could teach us. Differences of five
points are ordering aids, not meaningful precision. Scores need not sum to 100.

- 90–100: first-pass branch or essential baseline.
- 70–85: early extension or major competing explanation.
- 40–65: second-pass hypothesis requiring a reason to add complexity.
- 10–35: reserve branch.
- 0: outside the bounded programme, not logically impossible.

A high score for a baseline does not mean it fits the manuscript. Test it cheaply
or reuse existing evidence; do not rerun an already rejected configuration.
Scores apply to components, not whole cipher systems. They must not be added or
multiplied to rank combinations. Dependencies and joint predictions matter.

This is a broad operational taxonomy, not an enumeration of every conceivable
cipher. Families overlap, and bounded compositions generate further candidates.

## U. What plaintext unit is encoded?

| ID | Operation family | Priority | Reason |
|---|---|---:|---|
| U1 | Individual letters | 100 | Essential small-unit reference; separates glyph substitution from verbose letter coding |
| U2 | Letters plus selected letter pairs/doubles | 95 | Modest table extension; intermediate unit size with explicit parsing |
| U3 | Letters plus selected whole-word codes | 95 | Mixed coding can preserve lexical associations without a dictionary-sized table |
| U4 | Whole words | 85 | Direct route to page-associated vocabulary; codebook burden is measurable |
| U5 | Syllables | 75 | Intermediate unit size; requires declared Latin/Italian segmentation |
| U6 | Roots/stems plus grammatical endings | 60 | Could preserve lexical and morphological structure; more elaborate segmentation |
| U7 | Fixed pairs or short blocks only | 55 | Testable block structure; awkward word-boundary/padding conventions |
| U8 | Pronunciation units rather than spelling | 40 | Additional normalization ambiguity; distinct from written-letter substitution |
| U9 | Words plus selected stock phrases | 35 | Formulaic source material may justify a limited phrase list |
| U10 | Phrases as the primary units | 20 | Large lookup burden and weak constraints without a fixed inventory |
| U11 | Semantic concepts or paraphrase codes | 10 | Requires explicit recoverability standard; can easily become unfalsifiable |

U2, U3 and U9 are specified mixtures. An unrestricted mixture is not a candidate:
define which units get special codes, their inventory limit and parsing rule.

## R. How is a plaintext unit represented?

| ID | Operation family | Priority | Reason |
|---|---|---:|---|
| R1 | One glyph per unit | 100 | Cheap reference with strong equality-pattern constraints |
| R2 | Variable-length glyph string per unit | 95 | Allows verbose encoding; must demonstrate decodability |
| R3 | Structured code: prefix/core/suffix or comparable slots | 90 | Targets restricted word forms and boundary dependence |
| R4 | Fixed-length string per unit | 65 | Strong length/block predictions make it inexpensive to screen |
| R5 | Coordinate/table code with separately written components | 45 | Manual construction; test positional symbol classes |
| R6 | Output symbols jointly represent several adjacent units | 35 | Fractionation/composition requires an explicit inverse and grouping rule |
| R7 | Payload in selected positions of a cover text | 15 | Mask or extraction rule must be short and fixed before testing |

Representation does not determine spacing. For example, R2 can write one code
per apparent word or concatenate codes while retaining plaintext word spaces.

## M. How many encodings or meanings does a code have?

| ID | Operation family | Priority | Reason |
|---|---|---:|---|
| M1 | Fixed one-to-one substitution | 100 | Baseline and exact invariants |
| M2 | Several disjoint encodings per plaintext unit (homophones) | 95 | Core candidate; does not require a changing key |
| M3 | Alternatives selected by local context | 90 | Directly relevant to observed edge dependence |
| M4 | Same code has different meanings in a known state | 65 | Testable if the reader can determine state |
| M5 | Same code has multiple meanings resolved by language alone | 25 | Decoding ambiguity must be measured, not assumed away |

Variable-length codes need unique parsing or an explicit ambiguity rule even
when each individual code has only one meaning.

## S. What do visible spaces delimit?

| ID | Operation family | Priority | Reason |
|---|---|---:|---|
| S1 | Original plaintext words | 100 | Preserves lexical structure even under letter-level encoding |
| S2 | Individual code units | 100 | Crucial competitor: one apparent word could encode one letter or syllable |
| S3 | Mostly S1 or S2, with bounded splitting/joining | 95 | Spacing uncertainty materially affects existing results |
| S4 | Groups of codes under a short deterministic rule | 65 | Decouples visible words from plaintext units without arbitrary segmentation |
| S5 | Readability/line-filling groups independent of plaintext words | 45 | Test group-length and layout predictions |
| S6 | Spaces are themselves a payload channel | 15 | Requires manuscript-level reliability beyond current tokenization |

S3 modifies S1/S2 rather than replacing their underlying meaning. Model actual
scribal splitting separately from uncertainty introduced by a transcriber.

## K. Does the encoding table or state change?

| ID | Operation family | Priority | Reason |
|---|---|---:|---|
| K1 | Fixed table throughout the tested material | 100 | Simplest model and strongest information bounds |
| K2 | A few tables assigned to sections or scribes | 85 | Competes with topical explanations of page association |
| K3 | Small state controlled by local glyph/unit context | 80 | Can explain coupling; decoder must recover or infer state |
| K4 | A few tables with explicit switch markers | 65 | Recoverable change mechanism with detectable signals |
| K5 | Table/state resets at line, paragraph or page boundaries | 65 | Tests layout-linked structure without unlimited keys |
| K6 | Short periodic alternation of tables | 45 | Cheap periodicity tests; absence of a signal is not universal exclusion |
| K7 | Table selected by a keyword or external reference | 30 | Adds key assumptions and synchronization requirements |
| K8 | State updated from preceding plaintext/ciphertext | 25 | Autokey/running-state branch; chronology needs specific justification |
| K9 | Unconstrained fresh table for every page | 10 | Too flexible unless table generation and description length are bounded |
| K10 | Independent key or exception for every occurrence | 0 | Unrestricted form defeats informative ciphertext-only model selection |

Different homophones under one table are not, by themselves, multiple alphabets.
K2 is a hypothesis, not an inference that observed scribal differences are keys.

## Q. How are alternative encodings selected?

| ID | Operation family | Priority | Reason |
|---|---|---:|---|
| Q1 | Deterministic selection/no random choice | 100 | Baseline; necessary before assigning effects to randomness |
| Q2 | Independent choices with unequal stable probabilities | 95 | Allows habitual preferences without changing the key |
| Q3 | Context/position-dependent choice probabilities | 90 | Relevant to boundaries; complexity must be limited |
| Q4 | Uniform independent choice | 85 | Useful calibrated reference, but not the only random model |
| Q5 | Reuse bias, avoidance of recent choices or short memory | 75 | Tests repetition without replacing the plaintext by copied output |
| Q6 | Deterministic cycling through alternatives | 60 | Human-executable selection with testable serial structure |
| Q7 | Slowly changing preferences or a few regimes | 50 | Distinguish preference drift from a changing decoding table |
| Q8 | External randomizer such as dice/cards | 25 | Method of selecting outcomes; often indistinguishable from Q2/Q4 in text |

Q8 is not a separate observable distribution without extra constraints. Q5 may
select only valid encodings of the current plaintext unit; arbitrary copy-edit
generation is not automatically a reversible cipher.

## A. What happens before encoding?

| ID | Operation family | Priority | Reason |
|---|---|---:|---|
| A1 | Original spelling with explicit orthographic conventions | 100 | Baseline; keep period spelling instead of silently modernizing |
| A2 | Conventional contractions/abbreviations | 85 | Important source-model branch for manuscript prose |
| A3 | Restricted omission of predictable vowels or endings | 50 | Lossy unless recoverability is established |
| A4 | Reversible language-game transformations | 30 | Syllable moves/infixes can create structured forms; specify short rules |
| A5 | Lemmatization or phonetic simplification | 25 | Substantial information loss and additional linguistic assumptions |
| A6 | Paraphrase or semantic rewriting before encryption | 10 | Source flexibility rapidly overwhelms testability |

A1 can include separate arms for genuine period conventions such as u/v or i/j;
normalization choices must be recorded rather than tuned invisibly.

## T. Is order changed?

| ID | Operation family | Priority | Reason |
|---|---|---:|---|
| T1 | Preserve plaintext unit order | 100 | Baseline; fewest synchronization assumptions |
| T2 | Fixed local reversal, swap or permutation | 45 | Cheap invariant tests; invertible bounded neighbourhood |
| T3 | Reordering within fixed blocks | 35 | Preserves block multisets and may create periodic signatures |
| T4 | Line/column/page-route transposition | 25 | Requires layout and explicit treatment of irregular lengths |
| T5 | Interleaving two or more streams | 20 | Testable only with a bounded routing and recombination rule |
| T6 | Sorting/anagramming each word without recording order | 10 | Generally lossy; language-based reconstruction must be demonstrated |

Pure transposition is a cheap reference screen. Composition with substitution
is a distinct hypothesis; its failure cannot be inferred from either component
tested alone.

## L. What is added or changed at output and layout boundaries?

| ID | Operation family | Priority | Reason |
|---|---|---:|---|
| L1 | No additions | 100 | Essential comparison for every proposed extra rule |
| L2 | Boundary/line/paragraph markers | 95 | Directly addresses measured layout effects |
| L3 | Position-conditioned alternative shapes for the same code | 90 | Test modest allography without assigning new plaintext meanings |
| L4 | Deterministic adjustment at adjacent code boundaries | 85 | Potential source of coupling; preserve invertibility |
| L5 | Limited identifiable null glyphs or tokens | 65 | Decoder must recognize or infer them by a declared rule |
| L6 | Padding or filler selected to fit a line | 50 | Links length and layout with measurable constraints |
| L7 | Confirmation/repetition/check symbols | 30 | Possible redundancy mechanism; require a simple generation rule |
| L8 | Intentional decoy passages | 10 | Must delimit them independently; cannot discard difficult text ad hoc |

L4 includes reversible joining or alternate endings, not arbitrary deletion.
L3 does not assert that v101 distinctions carry previously undetected meaning.

## E. Observation model: mandatory, not a cipher family

| ID | Component | Priority | Reason |
|---|---|---:|---|
| E1 | Alternative transcriptions and uncertain spaces | 100 | Already known to affect measured results |
| E2 | Glyph grouping, ligatures and ordinary allography | 95 | Determines what counts as a symbol |
| E3 | Bounded copying/transcription errors | 85 | Avoid brittle exclusions; estimate or bound error rates independently |
| E4 | Damaged, uncertain and missing text | 80 | Preserve missingness and break adjacency appropriately |
| E5 | Rare marks/colour/placement as an extra channel | 15 | Needs image-based evidence; do not invoke to rescue a failed text model |

Observation errors must not become freely fitted exceptions at every mismatch.

## Whole-system investigation order

These are integrated research priorities, not sums of component scores or
probabilities that the manuscript used a system.

| Rank | System family | Priority | First discriminator |
|---|---|---:|---|
| 1 | Fixed mixed letter/pair/selected-word coding | 100 | Page association versus codebook size and vocabulary richness |
| 2 | Fixed letter coding with plaintext word boundaries retained | 95 | Equality/length constraints, then genre-matched joint fingerprints |
| 3 | Fixed verbose letter/pair coding with spaces between units | 90 | Information bound on page association; extend rather than repeat old grid |
| 4 | Fixed syllable coding | 80 | Unit/page information and repeat structure across source panels |
| 5 | Whole-word coding | 80 | Recurrence and lexical coverage at bounded codebook sizes |
| 6 | Limited changing-table versions of surviving/near-miss families | 75 | Whether a few states predict new pages rather than memorize them |
| 7 | Stem/ending coding with bounded contextual rules | 60 | Joint morphology, boundary dependence and recoverability |
| 8 | Substitution plus short local transposition | 40 | Invariants and held-out gains over substitution alone |
| 9 | Fractionated, periodic-key or route-transposition systems | 25 | Block/state structure and operational cost |
| 10 | Cover-text extraction, primary phrase or semantic codes | 10 | Independent extraction constraints and falsifiability |

Cheap invariant screens may be executed before a higher-ranked expensive model.
High priority does not license unlimited implementations: first determine which
branches a single discriminating test can address together.

Start by comparing the page information available in letters, letter pairs,
syllables and words of Latin/Italian source panels. Crucially, use a word-level
bound for systems retaining whole plaintext words, not a single-letter bound.
Mixed coding and changing-state systems require their own explicit bounds.

## Historical grounding and limits

The component taxonomy is informed by empirical research on historical keys,
including [Megyesi et al., Key Design in the Early Modern Era in Europe (2021)](https://ecp.ep.liu.se/index.php/histocrypt/article/view/165) and
[Somogyi's study of Italian cipher tables (2016)](https://ojs.ppke.hu/verbum/article/view/405).
The former spans 1400–1800: its full repertoire cannot be projected back to
early fifteenth-century Italy. Each implemented mechanism needs a more specific
historical assessment. These sources support the taxonomy, not the numerical
scores, which are project judgments.

The [Naibbe construction (2025)](https://www.tandfonline.com/doi/full/10.1080/01611194.2025.2566408) is a modern
constructive example relevant to verbose coding, not evidence of historical
use. The project's failed configurations remain failed; broadening a family
requires a declared change of assumptions and a new discriminating test.

No additional support for any cipher family was generated in preparing this
ranking. Revise priorities with a dated explanation when new evidence arrives.
