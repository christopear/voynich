# Voynich: structured codewords and local reuse

Stage 30, 9 October 2026. Evidence label: search found no fit in a bounded forward-model grid. No plaintext was recovered. The new test asks whether a small system for constructing codewords, combined with reusing alternatives locally, can match Voynich better than copy-and-modify text without a message.

The elementary slot construction has enough distinct outputs to hold the recipe dictionary, but its strings fail to reproduce the manuscript’s internal predictability. Persistence raises page association, sometimes too much. Neither the tested cipher nor the R2 comparison jointly fits the declared measurements. This is a limitation of these explicit constructions, not an exclusion of word codes, contextual ciphers, or message-free mechanisms in general.

## What was actually tested

One apparent ciphertext word per normalized Italian recipe word, two disjoint alternatives per word, a fixed dictionary across pages. Four policies: IID choice; one shared choice per page; one remembered choice per word per page; and the latter with a 25% chance of refreshing the choice on later occurrences. Each random choice is a fair bit. Only the last policy adds a refresh parameter; it was fixed in advance, not tuned after seeing results.

The glyph construction splits 2–10-glyph development words into first glyph, middle sequence and final glyph, then independently recombines bounded slot lists. It does not infer linguistic affixes or claim to reconstruct Voynich’s full word grammar. The middle list is bounded to 64 entries, with up to 16 entries at each edge. Random dictionaries are drawn from this construction; no key is optimized.

Both models learn from the same 512 development tokens on eight Currier B herbal folios. Eight different B folios are reserved for evaluation; IT, joined spaces and A are unchanged-setting sensitivities. R2 uses the existing six window/mutation/coupling settings. It runs continuously across pages, whereas cipher variant state resets per page. That difference is part of the declared competing mechanisms.

| Construction quantity | Value |
| --- | --- |
| Slot combinations | 14336 |
| Unique strings | 14336 |
| Collisions | 0 |
| Required dictionary entries / codewords | 1,484 / 2,968 |
| Maximum log2 support | 13.807 bits (not achieved entropy) |

| Panel | Tokens covered | Types covered | Previously unseen types covered |
| --- | --- | --- | --- |
| B_ZL_split_early | 70.5% | 56.1% | n/a |
| B_ZL_split_late | 54.9% | 42.6% | 28.4% |
| B_IT_split_late | 53.3% | 39.8% | 26.0% |
| B_ZL_join_late | 51.4% | 39.3% | 25.0% |
| A_ZL_split_late | 50.6% | 36.9% | 27.5% |

About 45% of the reserved B tokens lie outside this fitted grammar’s support. No assignment of its strings to plaintext words can represent those observed tokens without changing the grammar or adding exceptions. This support failure is specific to the frozen slot lists; it is not evidence against all slot systems.

## Local reuse solves only part of the problem

The following are development medians across both passages and all six keys. Page association and its role-conditioned version are permutation-corrected bits per apparent token. Glyph entropy is the conditional entropy of adjacent glyphs within words, without start/end symbols. A lower value means more predictable next glyphs; it is not a plaintext-recovery score.

| Policy | TTR | Top-ten share | Page association | Role-conditioned | Glyph entropy |
| --- | --- | --- | --- | --- | --- |
| iid | 0.562 | 0.225 | 0.053 | 0.022 | 2.761 |
| page | 0.540 | 0.233 | 0.301 | 0.164 | 2.770 |
| word_page | 0.544 | 0.236 | 0.297 | 0.159 | 2.746 |
| refresh | 0.545 | 0.231 | 0.180 | 0.096 | 2.730 |
| Voynich development | 0.613 | 0.209 | 0.115 | 0.086 | 1.981 |

The development selection chooses refresh, but even its median maximum scaled residual is about 3.0 (the descriptive neighbourhood ends at 1). One shared choice per page and per-word persistence overshoot page association. IID undershoots it. Refresh moves the role-conditioned score nearer the manuscript without repairing glyph predictability. No development draw in either family jointly fits all seven measures.

## Reserved-page outcome: neither model passes the joint screen

| Target | Frozen model | Joint hits | Best max residual | Median page association | Median glyph entropy |
| --- | --- | --- | --- | --- | --- |
| B_ZL_split_early | cipher | 0/12 | 2.81 | 0.180 | 2.730 |
| B_ZL_split_early | R2 | 0/6 | 1.80 | 0.140 | 2.500 |
| B_ZL_split_late | cipher | 0/12 | 2.49 | 0.193 | 2.781 |
| B_ZL_split_late | R2 | 0/6 | 2.19 | 0.187 | 2.639 |
| B_IT_split_late | cipher | 0/12 | 2.30 | 0.193 | 2.781 |
| B_IT_split_late | R2 | 0/6 | 2.27 | 0.187 | 2.639 |
| B_ZL_join_late | cipher | 0/12 | 2.42 | 0.193 | 2.781 |
| B_ZL_join_late | R2 | 0/6 | 2.54 | 0.187 | 2.639 |
| A_ZL_split_late | cipher | 0/12 | 2.39 | 0.193 | 2.781 |
| A_ZL_split_late | R2 | 0/6 | 2.21 | 0.187 | 2.639 |

The selected R2 configuration is level 2 with coupling enabled. For reserved B, Voynich glyph entropy is 2.072 bits, versus median 2.781 for the cipher and 2.639 for R2. R2’s lower-mutation configurations can approach the glyph entropy, but produce far too much page association and repetition. Choosing a different configuration separately for each measurement would not constitute one working model.

Twelve cipher validation draws mean two source passages × six keys, not twelve independent sources. R2 has six validation draws. Settings were frozen using development only. Secondary targets reuse the same generated sequences and recompute role-sensitive profiles on the target’s layout. These are sensitivity comparisons, not additional independent manuscripts.

## What the shuffle controls do—and do not—show

Equality at lags 1, 4 and 16 is measured along each page’s token stream, including across lines. Whole-word controls shuffle within page/role groups. Line controls move whole retained lines within paragraph-first-line classes, carrying their metadata. All retain page vocabularies. These diagnostics assess recurrence order, not grammar; neither positive nor negative values establish meaningful text.

| Panel/model | Control | Lag 1 excess | Lag 4 excess | Lag 16 excess |
| --- | --- | --- | --- | --- |
| B_ZL_split_early | word | 0.0109 | 0.0019 | 0.0044 |
| B_ZL_split_early | line | -0.0006 | 0.0031 | 0.0064 |
| B_ZL_split_late | word | -0.0000 | 0.0087 | -0.0044 |
| B_ZL_split_late | line | 0.0000 | -0.0003 | -0.0037 |
| cipher validation median | word | -0.0120 | 0.0118 | 0.0053 |
| cipher validation median | line | -0.0006 | 0.0032 | 0.0044 |
| R2 validation median | word | 0.0009 | -0.0014 | 0.0026 |
| R2 validation median | line | 0.0002 | -0.0024 | 0.0015 |

The original and reserved manuscript panels do not show a consistent positive effect across these lags and controls. R2 also has shuffle effects. We therefore do not use this recurrence diagnostic as a cipher-only property or claim an order-based distinction between language and message-free text.

## Capacity, state and key burden

The six dictionaries each contain 1,484 normalized recipe types with 2,968 codewords. The entire source vocabulary is known before evaluation; this is not unseen-word key recovery. UTF-8 JSON dictionary descriptions cost about 324,000 bits each; the grammar costs 11,440 bits. R2’s serialized trained model costs 215,984 bits. Serialization lengths are implementation-dependent accounting, not historical storage estimates or a calibrated minimum-description-length ranking.

The uniform ordered-assignment reference costs about 29,962 bits. It excludes dictionary spellings and is not the entropy of our weighted sampler. Do not add it to an explicit dictionary serialization as if these were independent costs. Neither a short PRNG seed nor an uncounted page choice makes a codebook free.

| Rule | Random-trajectory bits / 512 words | Peak stored variant bits | Realised variant-one fraction |
| --- | --- | --- | --- |
| iid | 512.000–512.000 | 0.000–0.000 | 0.479–0.545 |
| page | 8.000–8.000 | 1.000–1.000 | 0.250–0.750 |
| word_page | 387.000–388.000 | 52.000–54.000 | 0.453–0.547 |
| refresh | 498.919–529.938 | 52.000–54.000 | 0.455–0.578 |

The stored state count covers variant bits only: per-word memory also needs word identifiers or indexed dictionary slots and presence flags. Trajectory costs include fresh fair bits and refresh/no-refresh probabilities. They describe the sampled encoder path, not extra decoder key: disjoint codewords decode directly. The page policy has only eight independent choices per panel, so realised variant fractions can differ substantially from one half even though its marginal law is fair.

For a concrete additional state-storage budget, an indexed array with one valid flag and one variant bit per dictionary entry costs 2 × 1,484 = 2,968 bits for word-page/refresh, plus the shared dictionary and a page-reset rule. The page policy needs one persistent variant bit; IID needs none. This is a stated implementation convention, not a minimum memory or information bound, and is separate from the random trajectory’s probability cost.

## Calibration and verification

All 16/16 independent-key synthetic targets met the preregistered selection-reliability gate (max residual ≤2; minimum 12/16). This gate is deliberately distinct from the stricter descriptive manuscript neighbourhood ≤1. It validates coarse profile selection, not exact parameter identifiability or a calibrated family rejection test.

Leaving each development seed out gives 97.2% balanced accuracy distinguishing these simulated cipher/R2 profiles (gate 80%). This is a diagnostic on the sampled models, not classification of Voynich. A manuscript outside both model distributions cannot be identified by forcing it into the nearer class.

All 168 generated panels replay exactly; 49,152 cipher word tokens round-trip with known keys. All 16 calibration cases and 90 comparisons were recomputed. Stored profiles and order controls, source hashes and chapter/folio disjointness were checked.

Software validation: all 220 tests passed, including integration against the separate PostgreSQL test database. Source distribution and wheel builds passed; the CLI lists stages 01–30. No new Python dependencies were required.

Protocol committed at fc0c80e before execution. No grid expansion, changed threshold or post hoc model repair. Limits: one culinary source; only 512 tokens per target; fixed first/last-glyph slots; truncated middle inventory; random lexical assignment; no complete glyph-distribution likelihood, boundary-coupling test or semantic anchors. Large historical codebook feasibility remains unverified.

## What this changes for the next step

Do not spend more seeds tuning page persistence in this grammar. The next representational question is whether dependencies between codeword parts can predict unseen word forms while retaining enough unique codes. First measure that coverage/predictability tradeoff on frozen pages, without a new key search. Independently aligned visual labels remain the route to semantic constraints; neither this result nor a later structural match supplies a plaintext crib.

[Frozen protocol](../../docs/protocols/STRUCTURED_WORD_CODES_2026-10-09.md)

[Full evidence](evidence.json)

[All generated panels and audits](generated.json)

[Calibration](calibration.json)

[Verification](verification.json)

Reproduce into a new directory with python -m voynich.experiments.e30_structured_word_codes --output results/<new-dir>; then python -m voynich.laboratory.structured_verify --directory results/<new-dir> and python -m voynich.laboratory.structured_report --directory results/<new-dir>. Use uv run --locked for the project environment.
