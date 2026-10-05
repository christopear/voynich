# Voynich cipher research constitution

Status: agreed research direction, not a preregistered experiment.

Established: 26 September 2026. Evidence baseline: reviewed remote branch
`claude/gifted-wright-ctbvn0`, commit `5463771990097cab9cd0fdc7888d1aabf673be32`.
This document incorporates those findings; it does not claim that the local
checkout has been advanced to that commit.

## 1. Objective and working assumptions

Identify the simplest historically plausible, recoverable encoding process
that could have produced the manuscript, narrow the candidate families, and
accumulate discriminating evidence for surviving mechanisms.

For this programme we assume:

- The text is ciphertext. This is a working premise, not an established result.
- The source is Latin or Italian. Conclusions about plaintext depend on this
  restriction; failure of both does not exclude encryption in another language.
- The process is executable by hand with plausible tables, memory and labour.
- Currier B is the initial target. Currier A is a later transfer test, not
  silently pooled with B.

We seek advances beyond reproducing earlier project results. Negative results
are useful when they eliminate a clearly specified hypothesis or expose a
method's limits.

## 2. Construct the search space from operations

We cannot enumerate all possible ciphers. An unrestricted codebook or a rule
invented separately for every token could explain any finite text. We therefore
search bounded, explicitly specified families assembled from these choices:

| Component | Candidate choices |
|---|---|
| Plaintext unit | Letter, letter pair, syllable, word, phrase, defined mixtures |
| Cipher representation | Glyph, glyph sequence, apparent word |
| Alternative encodings | One-to-one, disjoint homophones, context-conditioned alternatives |
| Mapping state | Fixed, small finite state, line/page/section changes |
| Segmentation | Preserved word spaces, unit boundaries, output grouping |
| Additional operations | Nulls, contractions, boundary markers, bounded transposition |
| Random choices | Fixed independent probabilities, reuse bias, context/state-dependent selection |

Each candidate must specify an encoder and decoder, key/table size, state and
reset rules, permitted exceptions, and a probability law for random choices.
Information-losing abbreviation must explicitly state what can be recovered
and what ambiguity the reader must resolve. Verify round-trip recovery of the
claimed plaintext representation before treating a generator as a cipher.

History sets priorities: distinguish attested mechanisms, straightforward but
unattested manual combinations, and operationally implausible mechanisms.
Lack of historical attestation is not proof of impossibility. In particular,
do not categorically exclude changing alphabets or tables merely because a
particular named system is documented later. Record the evidence for historical
claims when introducing a candidate.

## 3. Findings that constrain the programme

- Currier B ending/next-initial dependence and hidden-boundary transfer survive
  multiple transcription analyses. These are structural findings, not evidence
  by themselves of meaning or a particular cipher.
- Different following contexts do not establish that r/l/n encode different
  plaintext units. Edge-conditioned homophones can produce this pattern.
  The v3 context-residual study did not decide their identity; do not resume
  versions of that test without a materially new source of identifiability.
- v101's larger boundary gain is chiefly explained by spacing differences.
  Segmentation is a model component and a source of measurement uncertainty.
- Additional v101 glyph distinctions have no demonstrated benefit under the
  tested procedures. This does not establish that all distinctions are noise.
- The latest benchmark rejected its tested configurations across seven cipher
  families and two message-free references. It did not exclude every possible
  member of those families.
- Page-associated vocabulary is a strong constraint. It is not automatically
  semantic topic structure: section, scribal practice and mapping changes may
  also produce it.

The baseline findings are recorded in `COUPLING_TEST_V3_FINDINGS_2026-09-26.md`,
`V101_FINDINGS_2026-09-26.md`, `V101_FOLLOWUP_FINDINGS_2026-09-26.md`, and
`CIPHER_FAMILY_FINDINGS_2026-09-26.md` at the baseline commit. Later corrections
take precedence over earlier summaries.

## 4. Prefer invariants and bounds to similarity alone

Look first for properties that hold for every key in a defined family:

- Bijective letter substitution preserves equality patterns and, if spaces
  survive, word lengths.
- Pure transposition preserves symbol counts within the transposition domain.
- Bijective word coding preserves token recurrence and word/page association.

For aligned plaintext unit U, ciphertext token C and page P, a fixed stochastic
encoder satisfying C independent of P given U obeys the data-processing bound:

    I(C; P) <= I(U; P).

This is a population statement, not an automatic inequality between noisy,
permutation-corrected estimates. It applies only after specifying the unit,
sampling scheme and output alignment. Multiple output tokens, regrouping,
nulls, context-dependent rules and changing tables require a new derivation.
If the encoder reads context or state, include that input explicitly; a bound
on the isolated letter cannot then exclude the expanded mechanism.

Distinguish exact invariants from properties estimated on a limited sample of
Latin/Italian texts. A corpus-derived ceiling is conditional on that source
model; it is not a theorem about every possible text in the language.

## 5. Statistical evidence and randomness

Randomness is part of a hypothesis, not an unrestricted rescue clause.

Before a confirmatory run, freeze the family definition, parameter limits,
plaintext sources, targets, segmentation arms, statistics, search procedure,
calibration, stopping rule and interpretation thresholds in a separate protocol.
The present constitution does not supply those experiment-specific thresholds.

- Fit on development data and evaluate frozen predictions on reserved data.
  Record earlier exposure: the manuscript has already been explored, so a new
  split must not be described as a historically untouched holdout.
- Search for the strongest plausible version of each family. Separate failures
  of the optimizer from evidence that no compatible parameter setting exists.
- Calibrate the entire fitting, selection and testing pipeline on synthetic
  targets, including targets near difficult parameter boundaries. A method must
  recover compatible families when their assumptions hold.
- Account for dependence within folios, source passages and repeated spellings.
  More seeds do not create more independent manuscripts or plaintext sources.
- Use joint acceptance criteria calibrated for the full collection of tests;
  do not promote isolated significant fingerprints into a family rejection.
- Distinguish rejection uniformly over allowed parameters from low average
  compatibility under a chosen parameter distribution. A finite grid supports
  only a grid-bounded claim unless additional mathematical bounds cover gaps.
- Report Monte Carlo uncertainty. Zero successes in simulated draws is not
  impossibility and does not constrain regions the sampler did not explore.
- Penalize or account for codebook size, state, exceptions and model selection
  through a declared predictive or description-length criterion. Do not invent
  uncounted per-page rules after seeing failures.

Use ZL, IT and v101 as sensitivity analyses of the same manuscript, not three
independent manuscripts. Treat uncertain spaces and glyph mappings explicitly.
Label post hoc results, protocol deviations and changes to interpretation.

## 6. Evidence labels

| Label | Required interpretation |
|---|---|
| Structurally excluded | An exact constraint fails under explicit assumptions, for every allowed key |
| Statistically rejected | A calibrated test rejects the stated family/domain with a specified error criterion |
| Search found no fit | No compatible setting was found; coverage or optimization remains uncertified |
| Compatible | Survives these tests; actual historical use is not established |
| Comparatively supported | Predicts reserved evidence better than alternatives with flexibility accounted for |
| Decipherment supported | Stable decoding yields coherent readings and independently checkable predictions |

No amount of matching a few aggregate statistics establishes a decipherment.
Keep a candidate ledger recording assumptions, search coverage, verdict,
binding evidence, surviving exceptions and the next discriminating test.

## 7. First study: encoding-unit size and page specificity

Question: can a fixed, page-independent encoding of Latin or Italian small
units retain enough page association to explain Currier B, or does a viable
model require larger units, contextual input or changing mappings?

This study constrains the architecture before investing in detailed glyph
codebooks. It extends the latest benchmark rather than repeating its grid.

### Initial competing families

| Family | Definition | Principal question |
|---|---|---|
| A: fixed small-unit coding | Letters or declared letter pairs, each yielding one apparent cipher token; fixed disjoint homophones allowed | Is available unit/page information sufficient? |
| B: fixed syllable coding | Declared Latin/Italian syllabification; one output token per syllable | Does a larger unit remove the information deficit? |
| C: word and mixed coding | Word codes or a bounded mixture of word codes and small-unit encoding | Can page association and vocabulary richness coexist under a manageable codebook? |
| D: limited changing mappings | Extend A/B with a bounded number of tables and an explicit selection/reset rule | Can a small, recoverable state explain the deficit without arbitrary page-specific keys? |

These are priorities, not an exhaustive partition. Letter substitutions that
retain whole plaintext words must not be confused with A: their visible tokens
can retain word-level page association. Record that architecture separately.

### Work sequence

1. Audit the existing page-information estimator and its sampling unit. Define
   comparable latent-unit and output-token statistics; distinguish true
   information bounds from finite-sample fingerprints. Check vocabulary pooling,
   rare types, page-size effects and transcription/spacing sensitivity.
2. Assemble documented Latin and Italian source panels. Prioritize herbal,
   medical and recipe material, including formulaic prose; retain narrative
   sources as contrasts. Record provenance, date, normalization and genre.
   Keep contiguous passages intact and use multiple independent sources.
3. Derive and validate fixed-channel bounds. Use controlled positive examples,
   including bijective word codes, to show that the procedure retains valid
   candidates. Test nulls and known violations so it does not mistake estimator
   bias or changing tables for a fixed-channel impossibility.
4. Measure how much page association letters, pairs, syllables and words carry
   under matched manuscript layouts. Separate variation within sections from
   variation between them. Use held-out passages/sources to assess generality.
5. Identify which fixed-channel families survive the conditional bounds. Where
   they fail, quantify the deficit and test bounded contextual or state-based
   extensions. Do not jump directly to an unrestricted per-page codebook.
6. Challenge survivors jointly with vocabulary richness, frequent-token share,
   local repetition, boundary dependence and line/paragraph effects. Matching
   page information alone is insufficient. Freeze models before evaluation.

### Required outputs and stopping decisions

Produce an experiment protocol, source manifest, estimator validation,
candidate ledger, reproducible results and a findings report with scoped claims.

- If the estimator or comparison is not reliable, resolve that before screening.
- If source choice dominates, report genre dependence and broaden the panel;
  do not claim to have excluded Latin or Italian.
- If fixed small units fail across the defined source/model domain, prioritize
  larger units and limited mapping changes, with that domain attached to the claim.
- If several families survive, choose the next experiment for its ability to
  distinguish them, not merely to improve their fit to already-used statistics.
- If all fail, revisit bounded assumptions explicitly; do not declare the cipher
  premise proved or disproved by an incomplete model catalogue.

## 8. Amendments

Keep this constitution stable across experiments. Record substantive changes
with their date, reason and whether they were motivated by observed results.
Experiment protocols may refine operational details, but must not silently
relax this document's evidence standards.
