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

Last updated 9 October 2026.

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
historical grid verdicts, but their pooled page-MI evidence requires an audit
before it is reused as a binding rejection reason; this round did not rerun
those grids or overturn their other fingerprints. The unpooled new signal survives.
