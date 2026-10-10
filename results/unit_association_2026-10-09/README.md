# Voynich: what the new round changes

9 October 2026. We have no supported plaintext reading. This round improves which hypotheses we can test: the synthetic parser bug is resolved for all eight fixtures, page-associated vocabulary survives stronger manuscript controls, and a vocabulary-pooling artifact is demonstrated and isolated.

| Question | Result | Meaning |
| --- | --- | --- |
| Did the parser fix work? | Correct parsing rule selected in 8/8 synthetic cases | Yes for parser selection; blind plaintext recovery is still only 28.5–75.0%. |
| Does Voynich retain page association? | 0.115 bits above within-section permutation baseline | Yes in this bounded sample; 0.092 after layout-role conditioning. This is not proof of semantic topics. |
| Which units look most promising? | Whole-word profiles sometimes overlap; letters and small mixed dictionaries fall short | Prioritise word/content-unit models, while retaining source dependence and joint fingerprint mismatches. |
| Can we use the old top-200 statistic as a bound? | No: tied rare types selected by page order create spurious association | The all-type primary result survives. Historical pooled comparisons need an audit, not automatic reversal. |
| Did we decrypt zodiac labels? | No; 299 labels inventoried and a falsifiable test scoped | Images and lexical anchors must be aligned independently before a semantic search. |

## The actual manuscript result

16 distinct Currier B folios: eight herbal and eight biological pages, first 64 clean tokens per page (1,024 total). Split and joined doubtful-space arms retain original line and paragraph roles. The numbers below are mutual information minus a matched permutation mean, measured in bits per apparent token. They are descriptive fingerprints, not probabilities of being correct, population information ceilings or percentages decrypted.

| Panel | Within section | Section + layout roles | 8-token block null | Type/token ratio |
| --- | --- | --- | --- | --- |
| voynich-split | 0.115 | 0.092 | 0.092 | 0.474 |
| voynich-join | 0.124 | 0.105 | 0.104 | 0.501 |
| word-shuffle-7 | 0.006 | -0.004 | 0.009 | 0.474 |
| glyph-shuffle-7 | -0.000 | -0.000 | 0.001 | 0.953 |
| word-shuffle-19 | -0.011 | 0.001 | -0.015 | 0.474 |
| glyph-shuffle-19 | 0.005 | 0.003 | 0.001 | 0.958 |
| word-shuffle-31 | -0.014 | -0.010 | -0.020 | 0.474 |
| glyph-shuffle-31 | 0.012 | 0.007 | 0.012 | 0.951 |

The herbal and biological subsets, measured separately, each give about 0.116 bits of excess within-section association. Joining doubtful spaces preserves the signal. Whole-word controls preserve vocabulary but disperse its page assignments within section/roles; glyph controls preserve each page’s glyph counts and word lengths. These controls reduce association substantially. Thus page glyph composition alone does not reproduce the observed recurrent-word association in these controls.

Monte Carlo standard error of the split-arm null mean is 0.0011 bits (199 permutations); the corresponding null SD is 0.0156. This is uncertainty in the computed null mean, not a confidence interval for the manuscript population. Block controls retain short local runs; they do not condition on line roles. No family-rejection p-value is claimed.

## What source-unit comparisons tell us

The next table shows ranges across three passage/layout seeds within each source, not confidence intervals or independent replications. Each unit becomes one apparent output word. The references match output-token count, so letters and words span different amounts of plaintext. Natural medical chapters and culinary headings are compared with artificial 256-word literary blocks. Mixed dictionaries come from a separate source partition and choose the 50 or 200 most frequent words; other words emit individual letters.

| Unit | Celsus | Pliny | Italian recipes | Alfonsi | Dante |
| --- | --- | --- | --- | --- | --- |
| letter | -0.022–-0.003 | 0.007–0.009 | -0.030–0.017 | -0.023–0.020 | -0.025–0.014 |
| pair | 0.024–0.060 | -0.010–0.039 | 0.004–0.054 | -0.007–0.084 | -0.002–0.062 |
| syllable | 0.016–0.052 | 0.006–0.065 | 0.015–0.097 | 0.074–0.099 | 0.044–0.101 |
| word | 0.055–0.093 | 0.023–0.076 | 0.063–0.146 | 0.080–0.144 | 0.048–0.100 |
| mixed50 | -0.000–0.032 | -0.037–0.029 | -0.000–0.013 | -0.023–0.020 | -0.003–0.028 |
| mixed200 | -0.023–0.027 | -0.023–0.028 | 0.011–0.039 | -0.014–0.055 | -0.029–0.014 |

Reference point: Voynich split = 0.115 bits, joined = 0.124. Letters reach at most 0.020, pairs 0.084, heuristic syllables 0.101, and frequency-selected mixed codes 0.055. These are observed profile gaps, not universal bounds. Whole-word Italian recipe and Alfonsi profiles straddle the manuscript value. Source choice matters: ancient medical word profiles are lower in these passages. Recipe text therefore changes the priority picture, but does not establish a medical plaintext or an Italian language identification.

A fixed bijective word code preserves token equality and raw empirical page MI exactly. We do not have to guess codeword spellings to assess that invariant. But an unrestricted codebook is not automatically recoverable, and a finite-sample permutation correction is not a bound on all stochastic encoders. Homophones, contextual coding, different token boundaries and changing tables were not exhaustively simulated here. A letter substitution retaining complete plaintext words belongs to the whole-word token comparison, not the one-letter/one-token arm.

## The apparent overlaps do not solve the joint problem

| Whole-word source | Within section | Section + roles | Type/token range | Top-ten share range |
| --- | --- | --- | --- | --- |
| celsus | 0.055–0.093 | 0.034–0.047 | 0.584–0.637 | 0.172–0.182 |
| pliny | 0.023–0.076 | 0.007–0.038 | 0.689–0.715 | 0.134–0.142 |
| cucina | 0.063–0.146 | 0.024–0.070 | 0.377–0.399 | 0.268–0.277 |
| alfonsi | 0.080–0.144 | 0.027–0.092 | 0.658–0.673 | 0.140–0.158 |
| dante | 0.048–0.100 | 0.033–0.049 | 0.498–0.531 | 0.225–0.237 |

Voynich split has type/token ratio 0.474 and top-ten share 0.186. Recipe whole-word profiles have fewer types (0.377–0.399); Alfonsi has more (0.658–0.673). Role-conditioned recipe association tops out at 0.070 versus Voynich’s 0.092. Assigning plaintext units to matching layout slots preserves margins but does not create a historically realistic layout-generating process. No source/model is declared jointly compatible by an uncalibrated checklist. Syllable segmentation is heuristic, and the narrow mixed arm does not test a dictionary of specifically medicinal content words.

## A measurement artifact found by the controls — post hoc

Frequency ties in the top-200 vocabulary were broken by first occurrence. Because input is grouped by page, the chosen rare types disproportionately come from early pages. Keeping that chosen vocabulary fixed during shuffling leaves the selection bias unaccounted for. A panel of entirely unique tokens gives 0.205 excess bits through this shortcut despite zero all-type excess. Identity-hash tie-breaking reduces that example to 0.00008–0.00136 bits.

| Panel | Original top-200 excess | Position-independent ties, range |
| --- | --- | --- |
| voynich-split | 0.187 | 0.119–0.133 |
| voynich-join | 0.199 | 0.127–0.134 |
| word-shuffle-7 | 0.049 | 0.006–0.009 |
| glyph-shuffle-7 | 0.171 | -0.002–0.000 |
| word-shuffle-19 | 0.018 | -0.014–-0.010 |
| glyph-shuffle-19 | 0.202 | 0.005–0.007 |
| word-shuffle-31 | 0.031 | -0.013–-0.009 |
| glyph-shuffle-31 | 0.165 | 0.012–0.012 |

The all-type primary comparison did not use pooling and is unchanged. Voynich still has association with position-independent ties. The older cipher-family fingerprint uses the same first-occurrence operation, but its 5,000-token windows and frequency cutoffs differ: this diagnostic has not measured the effect on every historical verdict. Historical numerical reports are preserved; pooled evidence must be audited before serving as a binding rejection reason.

[Post hoc diagnostic protocol](../../docs/protocols/UNIT_POOLING_AUDIT_2026-10-09.md)

## Synthetic calibration: what improved and what did not

All 177 admissible parsing policies were searched at the unchanged 4,096-evaluation beam budget each. Thirty-two searches were reused only after exact compatibility checks; 145 missing searches added 593,920 evaluations. Total represented budget is 724,992 evaluations. This is exhaustive over this parsing grid, not over substitution keys or all grouped ciphers.

| Fixture | Earlier recovery | All-survivor recovery | True parser selected | 90% gate |
| --- | --- | --- | --- | --- |
| italian-encoded-19 | 12.5% | 75.0% | yes | fail |
| italian-encoded-7 | 25.4% | 29.6% | yes | fail |
| italian-preserve-19 | 5.7% | 73.6% | yes | fail |
| italian-preserve-7 | 16.1% | 66.1% | yes | fail |
| latin-encoded-19 | 16.6% | 68.5% | yes | fail |
| latin-encoded-7 | 14.2% | 39.1% | yes | fail |
| latin-preserve-19 | 9.3% | 69.9% | yes | fail |
| latin-preserve-7 | 13.9% | 28.5% | yes | fail |

All eight winners now use the true parser, so their selected recovery equals recovery within the true-parser branch. The correct known key also has a better score than each returned solution. The evidence isolates a remaining optimisation shortfall under the fixed budget; it does not prove the scorer has the correct global optimum. Known-key round trips are exact, but the blind key search still fails all eight 90% gates. No additional original-page key search or transfer was performed, and the earlier f26r structural infeasibility result is unchanged.

Verification: all 177 database records and execution bindings checked; all 531 retained candidates replay exactly; all 64 synthetic spans independently decode through the trie decoder with the known keys. No evaluator exceptions. The calibration protocol was committed at 77b6819 before execution.

[Parser calibration evidence and verification](../parser_retention_2026-10-09/README.md)

## What I recommend reviewing before the next search

Prioritise a fixed word/content-unit hypothesis and image-linked predictions, rather than another increase in letter-key search budget. First align recurring labels to drawings and test their observable referents without forcing them to be zodiac sign names. Then, if defensible anchors exist, compare whole-word and bounded compositional codebooks with reserved lexical types and folios. A free codebook cannot decode unseen entries from a handful of cribs.

[Crib scope: assumptions, alternate referents and stopping rules](../../docs/protocols/CRIB_SCOPE_2026-10-09.md)

The zodiac inventory contains 299 labels, 271 clean under the current parser, and 22 whole-label spellings recurring across panels. This is not a plaintext dictionary. The label panels are a different domain from the Currier B paragraph sample. No semantic assignments have been fitted, and the needed image/label alignments remain unverified at glyph level.

## Reproduction and limitations

Software validation: all 208 tests passed, including PostgreSQL integration against the separate voynich_test database. Source distribution and wheel builds passed; the CLI discovers stages 01–27. The rendered report was visually checked.

The unit protocol and implementation were committed at 7f40ea6 before execution. Estimator gates passed: 50 IID panels averaged −0.0021 excess bits; 10 planted page-vocabulary panels averaged 0.3491. All 90 reference panels, both manuscript arms and six controls ran as declared. The pooling audit is explicitly post hoc, declared at 99780ae before its diagnostic execution. No manuscript cipher readings or statistical family exclusions are claimed.

Only ZL3b was measured in this stage; joining doubtful spaces is not cross-transcription replication. Sections are observational, not proven topics. Normalised modern editions differ from medieval spelling, abbreviation and manuscripts. Source chapters and arbitrary literary blocks differ from page breaks. The small 64-token pages are noisy; seeds are sensitivity draws, not independent corpora. Matched layout margins do not model plaintext/layout dependence. Population data-processing bounds remain conditional on a fixed page-independent aligned channel.

[Frozen unit study protocol](../../docs/protocols/UNIT_ASSOCIATION_2026-10-09.md)

[Raw numerical evidence](evidence.json)

[Source hashes and execution manifest](manifest.json)

[Source provenance, editions and licences](../../data/unit_association_sources/README.md)

Run in a full checkout copy, using a NEW output path: uv run --locked python -m voynich.experiments.e27_unit_association --output results/<new-dir>. Historical directories must not be overwritten. Post hoc audit: python -m voynich.experiments.posthoc_e27_pooling --source results/<new-dir> --output results/<new-audit-dir>. Prepared source chapters, exact manuscript slots, selected chapter IDs and offsets are exported for inspection.
