# Candidate ledger

The ledger the [research constitution](RESEARCH_CONSTITUTION.md) §6 asks for.
One row per hypothesis that has been tested or is queued. Labels use the
constitution's vocabulary. Update the row whenever a stage moves it, citing the
report, and record the date. Ordered from most to least constrained.

Labels used:
* **Excluded by capacity bound** — an information bound that holds exactly
  for every key fails, with estimated entropies and a wide margin. This sits
  between the constitution's "structurally excluded" (exact) and
  "statistically rejected" (calibrated error rate).
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
| 1 | One glyph (raw or compound EVA) → one letter, one fixed table, spaces kept (simple substitution, homophone merging of ≤ 2 glyphs per letter) | **Excluded by capacity bound** | Plaintext needs 1.0–2.4 bits more per 2–4-symbol window than Currier B can carry, for every key ([capacity screen](../results/capacity_screen_2026-10-09/README.md)); also fails the cipher-family fingerprints (F1/F2) | Latin (Celsus, Pliny, Alfonsi), Italian (Dante), German (MHG); normalised spelling; plug-in estimates with a large margin | None: stop searching this family |
| 2 | As 1, with two tables alternating by line, paragraph or page | **Excluded by capacity bound** | Gaps of +0.4 to +1.4 bits at n = 3–4, even after crediting one full bit of state per window | Same; more tables or per-word state need their own state budget | None for two tables; a many-table variant must first pass the screen |
| 3 | Manuscript searches of families 1–2 (9 Oct page pilot, line rotation, phase initialization) | **Search found no fit** | Better objective scores; competitive whole-word and line-shuffle controls; unstable mappings; no repeated readings ([pilot](../results/voynich_pilot_2026-10-09/README.md), [rotation](../results/line_rotation_2026-10-09/README.md), [phase](../results/phase_initialization_2026-10-09/README.md)) | Pages f26r, f31r, f39v | Superseded by rows 1–2 |
| 4 | Plain language or simple substitution, word spaces kept (F1) | **Rejected within grid** | Page-specific vocabulary, repetition, vocabulary shape ([cipher-family findings](reports/CIPHER_FAMILY_FINDINGS_2026-09-26.md)) | Tales, poetry and German texts, not page-topical herbals | Page-topical medieval herbal or recipe plaintext |
| 5 | Homophonic substitution of letters, word spaces kept (F2) | **Rejected within grid** | Far too many word types; no page-specific vocabulary | k = 40–90 symbols | Low priority |
| 6 | Nomenclator: homophonic letters plus up to 300 word codes (F3) | **Rejected within grid** | Vocabulary size, page-specific vocabulary | N ≤ 300 code words | Large-N word codes: row 12 |
| 7 | Scribal abbreviation, then substitution (F4) | **Rejected within grid** | Repetition, page-specific vocabulary | Fixed affix list | With a page-topical plaintext |
| 8 | Verbose letter/pair codes, fixed Naibbe tables, with or without nulls (F5, F7) | **Rejected within grid** | Almost no page-specific vocabulary (≤ 0.013 bits against Voynich's 0.2) | Fixed tables; Latin, Italian, German | Drifting tables: row 14 |
| 9 | Verbose syllable codes with a shared core (F6) | **Rejected within grid** | Page-specific vocabulary, repetition; its homophones would be trivially visible (AUC 0.9997) | h ≤ 8 variants | Low priority |
| 10 | Message-free assembly or copy-and-modify (R1, R2) | **Rejected within grid** | Assembly: no page-specific vocabulary; copy: vocabulary shape, line effects | Tested settings | Not a cipher hypothesis; kept as a control |
| 11 | v101 glyph variants are distinct letters | **Statistically rejected** (for d, y, k, r, sh, p) | No word-level information in variant choice, with calibrated power, including at the real minority rates ([V101](reports/V101_FINDINGS_2026-09-26.md), [follow-up](reports/V101_FOLLOWUP_FINDINGS_2026-09-26.md)) | f and cph not calibrated; v101 `A` is an o/a ambiguity | None |

## Open questions (not cipher families)

| Question | Status | Evidence |
|---|---|---|
| Do r/l/n endings encode different plaintext units? | Not decidable by context statistics on this corpus | [Coupling test v3](reports/COUPLING_TEST_V3_FINDINGS_2026-09-26.md) |
| What are the spaces? | Open. Coupling is about 6× stronger at doubtful spaces; transcriptions differ mainly there | [V101 follow-up](reports/V101_FOLLOWUP_FINDINGS_2026-09-26.md) |
| Do line and paragraph effects come from the cipher? | Every family needs an added layout convention to match them | [Cipher-family findings](reports/CIPHER_FAMILY_FINDINGS_2026-09-26.md) |

## Untested families, in priority order

| # | Candidate | Why it is open | Next test |
|---|---|---|---|
| 12 | Grouped-glyph or verbose codes with about 1.5–3 glyph units per letter, spaces inferred or treated as unit boundaries (operations U1/U2 + R2/R3 + S2/S3) | Passes the capacity bound by construction; no manuscript search yet | Calibrate the `groups`/`mixed` solver on Voynich-like fixtures, then a bounded manuscript trial with controls |
| 13 | Word or mixed codes: letters plus a bounded word-code list, or whole-word codes (U3/U4) | Can keep page-specific vocabulary; consistent with the vocabulary shape | Constitution §7 first study (unit size × page-specific vocabulary) |
| 14 | Verbose codes with section- or page-drifting tables or preferences (K2/Q7) | The only route for letter-level codes to create page-specific vocabulary | Extend the cipher-family benchmark with drift; check the page-specificity fingerprint |
| 15 | Syllable codes without a shared visible core | Larger unit; F6's failure was tied to its shared-core design | After rows 12–13 |
