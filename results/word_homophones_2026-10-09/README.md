# Word-code alternatives: a useful constraint, no decipherment

9 October 2026. The suggested recipe-word experiment is complete. Independent random alternatives improve vocabulary size and common-word share, but none of the seven tested settings matches those properties AND page association together on the original manuscript panel. Meanwhile, page association replicates in IT2a and on 16 additional folios. The earlier cipher-family verdicts also survive the pooling audit.

| Question | Finding | Consequence |
| --- | --- | --- |
| Can two spellings per recipe word fix the mismatch? | They bring the vocabulary measures closer, but measured page association falls short | Simple IID alternatives are not sufficient for these sources/passages. Word codes in general remain open. |
| Does the manuscript signal replicate? | Yes: original ZL 0.115 bits vs IT 0.123; additional pages ZL 0.104 vs IT 0.097 | The signal is not peculiar to one transcription or the original folio set. |
| Did pooling invalidate the old grid verdicts? | No: every ZL configuration/window cell still fails unchanged shape metrics or audited page MI | The scoped audit warning can be cleared for the original ZL verdicts. |
| Can the proposed crib validation proceed? | Only four label types cross the frozen folio split; minimum was five | Prepare alignment candidates, but do not lower the semantic-test gate after inspecting the count. |

## What was tested

Three sources: Italian culinary recipes, Celsus and Pliny. Each source word has one, two or three disjoint opaque codewords. Choices are independent of page, layout and earlier choices, using the seven probability vectors below. One source word produces one apparent ciphertext word; codeword glyph structure is not modelled. Separate chapter halves supply development and validation passages. Two passage seeds per half and six encoding draws give 504 panels of 1,024 tokens. No cipher keys were searched, and no Voynich words were assigned meanings.

The protocol and producing code were committed at 55c7a8f before execution. All 14 independently generated positive-control targets passed the declared neighbourhood calibration. Some different probability settings are indistinguishable on these fingerprints: passing calibration does not identify the number of historical homophones.

## The trade-off in the recipe model

| Alternative probabilities | Types / tokens | Top-ten share | Page association | After layout roles |
| --- | --- | --- | --- | --- |
| Voynich original | 0.474 | 0.186 | 0.115 | 0.092 |
| 100% | 0.362 | 0.273 | 0.061 | 0.027 |
| 90% / 10% | 0.413 | 0.246 | 0.054 | 0.022 |
| 75% / 25% | 0.446 | 0.226 | 0.042 | 0.014 |
| 50% / 50% | 0.463 | 0.207 | 0.031 | 0.006 |
| 80% / 10% / 10% | 0.460 | 0.223 | 0.044 | 0.016 |
| 60% / 20% / 20% | 0.507 | 0.198 | 0.034 | 0.010 |
| 33% / 33% / 33% | 0.529 | 0.177 | 0.029 | 0.008 |

Two equally likely alternatives give a type/token ratio of 0.463 (Voynich 0.474) and top-ten share 0.207 (Voynich 0.186). But page-association excess is only 0.031 (Voynich 0.115), falling to 0.006 after conditioning on line/paragraph roles (Voynich 0.092). Three alternatives can also improve the first two quantities without repairing the latter two. These are medians over two passages and six draws, not independently replicated manuscripts.

This is not a statement that random homophones destroy underlying information. With disjoint codes, the source word U is a deterministic function of the code C. With page-independent choices, data processing in both directions gives I(C;page)=I(U;page) in the population. The permutation-excess statistic changes because independent choices split repeated observations across rarer types. The experiment tests finite-sample recurrence fingerprints, not a violation of that identity.

## Joint selection and prospective transfer

The four screening scales were fixed at 0.05 for type/token ratio, 0.04 for top-ten share, and 0.05 bits each for section and role-conditioned excess MI. A joint hit requires every absolute difference to fit its scale. These are descriptive neighbourhoods, not calibrated rejection thresholds. One setting per source was selected on the original ZL target from median development fingerprints, then frozen for all other comparisons. No setting was reselected on IT2a or additional pages.

| Source | Selected probabilities | Development max-scaled distance | Original ZL hits / 12 | Additional ZL hits / 12 | Additional IT hits / 12 |
| --- | --- | --- | --- | --- | --- |
| cucina | 90% / 10% | 1.514 | 0 | 0 | 0 |
| celsus | 100% | 2.871 | 0 | 6 | 0 |
| pliny | 100% | 3.848 | 0 | 0 | 0 |

No development draw from any source/configuration is a joint hit. The selected recipe setting is 90/10, but its median distance is 1.514, outside the neighbourhood, and it has zero hits on original ZL, joined-space ZL, IT or additional-page targets. This is a no-joint-match result for this bounded screen, not a statistical exclusion of word coding.

Celsus without alternatives falls inside the additional-ZL neighbourhood for one of two validation passages (six identical encoding-seed records), but fails the original panel and additional IT. This is one passage, not six independent successes. The broader lesson is source and section dependence: we cannot identify a recipe/medical plaintext genre from the earlier overlap. The chapter-disjoint design changed the recipe passages relative to stage 27; the baseline profile is consequently different and source sampling remains important.

## Actual manuscript replication

| Panel | Types / tokens | Top-ten share | Page association | After layout roles |
| --- | --- | --- | --- | --- |
| ZL_original | 0.474 | 0.186 | 0.115 | 0.092 |
| ZL_joined | 0.501 | 0.184 | 0.124 | 0.105 |
| IT_original | 0.490 | 0.189 | 0.123 | 0.094 |
| ZL_additional | 0.567 | 0.129 | 0.104 | 0.080 |
| IT_additional | 0.585 | 0.119 | 0.097 | 0.077 |

Original panel: 16 distinct herbal/biological folios. Additional panel: eight different herbal folios and eight starred-text folios; there are not enough remaining biological folios for a second matching set of eight. Thus the additional panel tests a new section mix, not an identical population. Each panel uses 64 clean tokens per page. IT2a uses the same pages, but not exact token/glyph alignment; it is a sensitivity analysis of the same manuscript, not another manuscript.

Within-section excess association is 0.115/0.123 in original ZL/IT and 0.104/0.097 on additional ZL/IT. Role-conditioned values are 0.092/0.094 and 0.080/0.077 respectively. Page-associated vocabulary remains a robust target for future models; it still does not establish semantic topic, cipher status or a plaintext reading.

## The historical pooling audit is closed for the ZL verdicts

| Window | Original first-occurrence pool | Position-independent lexical ties | No vocabulary cap | Every original grid cell remains negative |
| --- | --- | --- | --- | --- |
| W1 | 0.211 | 0.210 | 0.255 | True |
| W2 | 0.189 | 0.189 | 0.186 | True |

Audit coverage: 228 configuration cells per window, 456 in total. Of these, 434 already fail P1–P4, which pooling cannot affect. The remaining 22 cells were resimulated at all six original seeds: 132 runs. Their original page-MI values and the original target/bootstrap values reproduced exactly. With freshly recomputed target bootstrap SDs, every remaining cell fails page MI under both position-independent ties and no cap. This proves the old ZL conjunction verdicts unchanged without needing all other capped fingerprints to be unchanged.

This independently supports Claude’s overall audit conclusion, but is not a replication of all his reported decimals or the claimed maximum P5/P7–P9 shifts. Our tie rule is lexical identity, not an unspecified scratch-script rule. IT/v101 full-grid verdicts and old calibration gates were not rerun. The stage-27 small-sample pooling artifact remains real; the sufficient audit closes the specified old-ZL concern, not a general approval of first-occurrence pooling.

[Audit protocol](../../docs/protocols/HISTORICAL_POOLING_AUDIT_2026-10-09.md)

[Audit evidence](../historical_pooling_audit_2026-10-09/evidence.json)

## Recurring labels: preparation without forced meanings

Only otaly, okeoly, okydy and okaram cross the proposed development folios 70–71 / reserved folios 72–73 split. The scope specified five anchor types; that gate is not met. The 22 recurring types have 53 occurrences in total. The coordinate packet keeps exact spelling candidates for each occurrence, including missing and ambiguous matches, without pretending that a cached token box is a verified illustrated referent. No fuzzy spelling equivalences, image-coordinate transformations or lexical guesses were invented.

[Alignment review packet](../label_alignment_2026-10-09/report.html)

Image/label correspondence remains to be verified manually. A future protocol could use additional label domains or a different justified validation design, but this round does not silently change the reserved split or its threshold. No semantic crib test was run.

## Next discriminating hypothesis

Independent random alternatives alone are insufficient here. I would next compare a narrowly bounded mechanism that reuses an alternative within a page or local passage against IID choice, with the same codebook size and marginal alternative frequencies. That changes recurrence while remaining hand-executable in principle. Page-specific choice can itself create association, so it must be charged as state and tested on reserved pages; a successful fingerprint fit would still not be a reading. Content-selected medicinal word lists and genuine layout generation remain separate hypotheses, rather than additions silently piled onto this model.

Before semantic search, finish the label-image alignment and establish an adequately powered reserved prediction set. Do not increase letter-solver budget as a substitute. No historical key-size bound was imposed: the full-source recipe dictionaries have 1,484/2,968/4,452 codewords for one/two/three alternatives; Celsus and Pliny dictionaries are much larger. Practical codebook size, glyph-level capacity and internal word structure remain untested constraints.

## Validation and reproduction

All 504 ciphertext panels replay exactly and all 516,096 word tokens round-trip with known keys. All five manuscript panels were independently recomputed; chapter/folio separation and execution input hashes verified. These are synthetic known-key checks, not percentages of Voynich decrypted. The full 211-test suite, including PostgreSQL integration, passed. Source and wheel builds and CLI discovery were checked.

[Verification](verification.json)

[Frozen protocol](../../docs/protocols/WORD_HOMOPHONES_2026-10-09.md)

[All draw-level results and joint residuals](evidence.json)

[Execution/source hashes](manifest.json)

Rerun in a full checkout with a new directory: uv run --locked python -m voynich.experiments.e28_word_homophones --output results/<new-dir>. Replay: python -m voynich.laboratory.word_homophone_verify --directory results/<new-dir>. Historical audit: python -m voynich.experiments.posthoc_e24_pooling_audit --output results/<new-audit-dir>. No new dependencies or manuscript key searches were needed.
