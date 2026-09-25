# Voynich Manuscript — Cryptanalytic Continuation Brief

> **Status note (25 September 2026).** This is the original handoff, preserved
> unchanged below. Check its numbers against the later documents before citing them:
>
> * **Reproduced exactly:** §4.3 internal m, §4.4 r/l 16/48, §6.1–6.3 decomposition,
>   cut positions and alternations, §6.4 hidden-boundary prediction, §8.2 Naibbe
>   localization, §14 homophone recovery, §16 raw first-token uniqueness.
> * **Reproduced within noise or approximately:** §4.2, §7, §8.3, §9, §10, §15.
> * **Definition-dependent:** §11 lattice counts and §13 OK/OT effect sizes.
> * **Not reproduced; do not cite:** §4.1 contextual cosines. The §9 edge-pruning
>   control has no recorded definition.
> * **§8.2:** the 646 vs 634 discrepancy comes from the denominator
>   (`RECONSTRUCTION_FINDINGS_2026-09-25.md`).
> * **"Sandhi":** `REVIEW_2026-09-24.md` explains why the term overstates the evidence.
> * **Later results:** the terminal/next-initial effect generalizes mainly in
>   Currier B, and a message-free generator reproduces it
>   (`FRONTIER_FINDINGS_2026-09-24.md`, `MECHANISM_FINDINGS_2026-09-24.md`).
> * **§19:** now run (`EQUIVALENCE_FINDINGS_2026-09-25.md`). It works on
>   Naibbe-family ciphers, but it gives no evidence of Voynich homophone classes.
> * **§4.4 qualified:** distinct following-initial distributions for r/l are
>   also exactly what edge-conditioned homophony produces
>   (`COUPLED_CIPHER_FINDINGS_2026-09-25.md`). r/l carry information about the
>   next word; whether they encode different plaintext is open.

**Purpose:** handoff document for continuing the analysis in Codex without losing the experimental state, negative results, or methodological corrections already established.

**Current corpus/transcription:** René Zandbergen / Gabriel Landini **ZL3b**, version dated **13 May 2025**, IVTFF/EVA transcription, obtained from the `matthewdgreen/cipher_benchmark` mirror.

**Primary working subset for controlled experiments:** Herbal section, Currier A, Hand 1. This gives **95 pages** in the parser used here. f3r was repeatedly held out when testing hypotheses developed on the other pages.

---

## 1. Executive state of play

We have **not deciphered or semantically translated** the Voynich Manuscript.

The main progress is representational: the object to be deciphered is increasingly unlikely to be “EVA word = plaintext word” or “EVA character = plaintext character.” The evidence supports a layered surface system with at least the following components:

1. **Latent units can be joined inside a single written Voynich token.**
2. **Terminal states (`n/l/r`, with `m` strongly boundary-associated) are context-sensitive.**
3. **The terminal on one unit depends partly on the initial of the next latent unit.**
4. **Physical line endings modify the surface realization of terminals.**
5. **Several prefix/remainder lattices (especially `OK/OT × remainder`) behave compositionally.**
6. **Some same-remainder prefix variants may be near-equivalent/homophonic; others preserve real contextual distinctions.**
7. **Naibbe, a known verbose homophonic cipher, is an excellent positive control:** the segmentation method developed from Voynich recovers real hidden Naibbe token boundaries extremely well, while some specifically Voynich terminal behaviour does *not* transfer to Naibbe.

The current best broad hypothesis is therefore:

> **Voynichese is a highly structured surface encoding/notation layer, plausibly a context-sensitive verbose homophonic cipher or related technical shorthand system, over a meaningful latent sequence.**

That is still a category-level hypothesis, not a solved cipher.

---

## 2. Data source and parsing conventions

### Voynich transcription

Mirror used:

`https://raw.githubusercontent.com/matthewdgreen/cipher_benchmark/main/benchmark/unsolved/sources/voynich/transcriptions/ZL3b-n.txt`

The transcription contains page metadata such as section, Currier language, hand, labels, paragraph starts, etc.

### EVA glyph units

For analyses requiring “character” boundaries, do **not** naïvely split EVA into ASCII characters. Treat the following compounds as single visual/transcription units before falling back to single characters:

- `cth`
- `ckh`
- `cph`
- `cfh`
- `ch`
- `sh`

This is still only an approximation to true glyph structure, but it is better than treating every EVA ASCII byte as an independent plaintext-like character.

### Body token parsing

The code in this handoff removes IVTFF control markup, alternate-reading markup, comments, and punctuation, and uses only loci containing paragraph text (`P` in the locus descriptor).

Because punctuation and `<->` joins can be parsed in slightly different ways, page-level raw token counts in earlier scratch work varied by a few tokens. The code here is the canonical handoff implementation.

---

## 3. Initial literature-informed attack and negative results

### What previous work already established

Important pre-existing directions included:

- Currier A/B statistical varieties and line-position effects.
- Friedman/Tiltman classical cipher analysis.
- Language/statistical structure: Reddy & Knight; Montemurro & Zanette; Bowern/Lindemann.
- Automated decipherment/language-ID attempts such as Hauer/Kondrak.
- Plant-label / known-word approaches such as Bax.
- Generated/hoax models such as Rugg and Timm/Schinner.
- Slot-grammar / positional morphology approaches.
- Recent verbose-cipher work, especially Greshko’s **Naibbe** cipher.
- A 2026 computational project reporting an `n/l/r` terminal system and following-token conditioning.
- 2026 positional-entropy work suggesting verbose substitution can reproduce unusual Voynich information-theoretic signatures.

### Simple substitution attacks failed

A monoalphabetic substitution model trained against Latin character trigrams can make a single page look pseudo-Latin, but the “Latin” is optimizer hallucination. Typical properties:

- self-fit trigram likelihood can approach held-out Latin;
- actual Latin dictionary-word recovery remains tiny;
- mappings transfer poorly to another Voynich page.

A homophonic substitution model improves character-level LM likelihood further but collapses many Voynich glyphs to a small number of plaintext letters and still does not recover semantics.

**Conclusion:** language-model fit alone is not a decipherment criterion. Any future semantic decoder must be reversible, cross-page, and evaluated on withheld material.

### Plant crib falsification

A tempting crib such as `ytoail = CYANUS` under simple substitution implies implausible patterns elsewhere (e.g. `daiin -> ?nuu?` under that mapping). This was treated as a falsification of the *specific substitution crib*, not of the plant identification or all possible encryption schemes.

---

## 4. Terminal system: strongest replicated structural result

### 4.1 Same-stem terminal families

Many forms differ only in a terminal glyph and have unusually similar contexts, e.g.:

- `chor / chol / chom`
- `char / chal / cham`
- `cheor / cheol / cheom`
- `otar / otal / otam`
- `okar / okal / okam`
- `qokar / qokal / qokam`

Earlier contextual-cosine examples from the full corpus included approximately:

- `chor/chol`: 0.737
- `otchor/otchol`: 0.716
- `chom/cham`: 0.658
- `shor/shol`: 0.653

Matched unrelated pairs were substantially lower on average.

### 4.2 `m` is strongly line-boundary associated

Across body text, `m` endings are massively enriched at physical line ends.

Representative aggregate same-stem result:

- same-stem `m` forms: ~**68.5%** line-final
- corresponding `r/l` sibling forms: ~**7.9%** line-final
- enrichment: ~**8.7×**

Strong families included:

- `dar / dal / dam`
- `otar / otal / otam`
- `okar / okal / okam`
- `qokar / qokal / qokam`
- `char / chal / cham`
- `chor / chol / chom`
- `cheor / cheol / cheom`

This effect persisted across Currier A, Currier B, and multiple hands.

### 4.3 `m` is not *only* line-final

A later correction was important: internal `m` cannot be left untreated.

Among internal `m` tokens, roughly **85.4%** had an attested same-stem `n/l/r` sibling. This means `m` appears to belong to the same terminal system even away from physical line ends, while being *especially* favoured at line boundaries.

Do **not** permanently collapse `m` to a specific `r` or `l`. The latent interpretation is better thought of as a terminal state whose surface realization is strongly boundary-conditioned.

### 4.4 `r` and `l` are not interchangeable

A permutation test on 48 sufficiently frequent same-stem `r/l` families showed that **16/48** had following-word initial distributions beyond the 95th percentile of random relabellings.

Large examples included:

- `dar/dal`
- `or/ol`
- `qokar/qokal`
- `otar/otal`
- `cheor/cheol`
- `chor/chol`

Therefore **do not merge `r` and `l`** in the final latent state. They carry real information.

---

## 5. Terminal “sandhi”: dependence on the next unit

For tokens ending `n/l/r`, terminal choice depends partly on the initial glyph of the following token.

A stem-preserving permutation test was used:

- preserve each stem’s own `n/l/r` preference exactly;
- shuffle following initials only within that stem;
- compare observed terminal↔next-initial mutual information to the null.

### Full manuscript result

Within physical lines:

- observed MI ≈ 0.0886 bits
- shuffled mean ≈ 0.0292 bits
- **excess ≈ +0.0594 bits**
- permutation **p ≈ 0.0033**

Across physical line boundaries:

- excess ≈ +0.0019 bits
- **p ≈ 0.28**

So the terminal knows something about the next unit **only while both remain within the same physical line**.

A weaker left-context effect also exists, but is much smaller than the following-unit effect.

This independently reproduced a recent 2026 computational result on a different transcription.

---

## 6. Hidden boundaries inside written tokens

This became one of the strongest new connections in the project.

Examples from f3r:

- `chololy -> chol · oly`
- `otaldam -> otal · dam`
- `sheoldam -> sheol · dam`
- `cholcthom -> chol · cthom`
- `pcheoldom -> pcheol · dom`

### 6.1 Rare-token decomposition

Among **3,250 rare long forms** (frequency <= 2, at least six EVA glyph units):

- **51.1%** could be split into two independently frequent corpus tokens.

Interior-glyph shuffle null, preserving the first and last glyph:

- only **4.7%** remained decomposable.

Observed/null ratio: roughly **11×**.

### 6.2 Boundaries strongly prefer terminal positions

Across all candidate internal cut positions in rare long forms:

- after `n/l/r/m`: **51.8%** yield two frequent units
- after any other glyph: **7.8%**

Rate ratio ≈ **6.6×**; odds ratio ≈ **12.7×**.

This links hidden segmentation directly to the same terminal system found at visible word boundaries.

### 6.3 Exact joined/spaced alternations

Among 1,661 decomposable rare forms, **359 (21.6%)** have an exact `A B` spaced realization elsewhere in the manuscript.

Examples:

- `daraiin <-> dar aiin`
- `chydaiin <-> chy daiin`
- `sholdaiin <-> shol daiin`
- `darchor <-> dar chor`
- `chololy <-> chol oly`
- `otaldam <-> otal dam`

Direction control:

- forward-only `A B`: 234 forms
- reverse-only `B A`: 97 forms
- total forward adjacency occurrences / reverse ≈ **1.66×**

Thus this is not merely frequent components appearing in either order.

### 6.4 Hidden boundaries obey the same terminal-conditioning rule

This is probably the strongest potentially novel connection.

Train terminal choice **only on visibly spaced pairs**. Then test the terminal at independently inferred hidden boundaries inside joined tokens.

On **624** evaluable joined boundaries:

- stem-only terminal prediction: **63.9%**
- stem + following latent unit initial: **70.8%**

Therefore the proposed hidden boundary behaves functionally like a visible boundary.

---

## 7. Probabilistic / Viterbi segmenter

A boundary model was calibrated using held-out pages instead of f3r intuition.

### Synthetic held-out benchmark

Take a genuine held-out spaced pair `A B`, concatenate to `AB`, and ask the model to recover the boundary using training-page frequencies.

Among 257 ambiguous cases where multiple candidate boundaries were possible:

- true boundary recovered ≈ **90.7%** with a modest terminal-boundary bonus.

### Split-vs-unsplit likelihood ratio

The useful scoring idea is:

`score(split) = log P(A) + log P(B) + boundary_bonus`

versus

`score(unsplit) = log P(AB)`

and split only if the likelihood-ratio exceeds a threshold learned on other pages.

Using **real written Voynich tokens** as the negative class, held-out testing gave approximately:

- sensitivity: **83.9%**
- specificity: **91.6%**
- balanced accuracy: **87.7%**
- among accepted positive cases, boundary location ≈ **99.3%**

### f3r Viterbi pass

With f3r excluded from training frequencies:

- 114 written tokens
- 126 inferred latent units
- 12 tokens split

Examples automatically recovered:

- `qocheor -> qo · cheor`
- `chololy -> chol · oly`
- `otaldam -> otal · dam`
- `sheoldam -> sheol · dam`
- `cholcthom -> chol · cthom`
- `okadaiin -> oka · daiin`
- `qodair -> qo · dair`
- `shodaiin -> sho · daiin`
- `otolom -> otol · om`
- `qosaiin -> qo · saiin`

Very low-margin splits should remain tentative.

---

## 8. Naibbe positive control

This was the most valuable recent advance.

Repository:

`https://github.com/greshko/naibbe-cipher`

Relevant files:

- pre-respacing cipher: `encrypted/nathist_output_ciphertext.txt`
- post-respacing cipher: `encrypted/nathist_output_ciphertext_respaced.txt`
- known pre-encryption plaintext-unit stream: `respaced_plaintext/nathist_pre_encryption_respaced_plaintext.txt`
- decrypted stream: `decrypted/nathist_output_ciphertext_decrypted.txt`

### 8.1 Ground-truth erased spaces

Naibbe deliberately removes ~3% of ciphertext spaces by concatenating neighbouring cipher tokens.

In the Natural History sample:

- post-respacing tokens: **33,750**
- true compound ciphertext tokens: **985** (~2.92%)
- two-part compounds: **957**
- 3+ part compounds: 28

The alignment between pre- and post-respacing files is exact.

### 8.2 Voynich-style splitter on Naibbe

Using only ciphertext and hiding the true deleted boundaries:

- evaluable two-part compounds: 646
- boundary localization accuracy: **97.8%**
- compound-vs-single cross-validated balanced accuracy: **~82.7%**
- accepted-boundary accuracy: **~99.6%**

Importantly, the Voynich-specific `n/l/r/m` boundary bonus did **not** materially improve Naibbe.

Interpretation:

- the general segmentation method transfers to a known verbose cipher;
- the terminal system appears more Voynich-specific, not an inevitable property of verbose ciphers.

### 8.3 Information trajectory through a known cipher

Naibbe adjacent-unit excess MI:

- post-space-deletion ciphertext: ~**0.088 bits**
- original cipher-unit stream: ~**0.096 bits**
- known plaintext-unit stream: ~**0.648 bits**

Voynich Herbal-A/Hand-1 sequence:

- surface: ~**0.074 bits**
- segmented: ~**0.089 bits**
- normalized: ~**0.117 bits**

This strongly suggests that current Voynich normalization is analogous to removing **early cipher-layer distortions**, not recovering plaintext.

---

## 9. Vocabulary collapse controls

A key concern was that mutual information would rise trivially whenever vocabulary is merged.

Herbal-A/Hand-1 type counts:

- surface: **2,468**
- segmented: **1,991**
- normalized: **1,640**

Full-sequence adjacent-unit excess MI:

- surface: ~0.074
- segmented: ~0.089
- normalized: ~0.117

Random type-collapse to the same **1,640** classes:

- mean ~**0.087**
- ~95% interval ~0.081–0.093

Random edge-pruning control:

- ~0.049

Thus the increase to ~0.117 is not simply due to having fewer categories.

---

## 10. Internal glyph statistics remain cipher-like

Matched-window character/glyph conditional entropy shows that raw and partially normalized Voynich remain much closer to Naibbe than to ordinary Latin/Italian at the local symbol level.

Approximate 3,000-token-window values:

| Representation | H(next|1 glyph) | H(next|2 glyphs) |
|---|---:|---:|
| Voynich surface | 2.219 | 1.824 |
| Voynich normalized | 2.090 | 1.628 |
| Naibbe | 2.009 | 1.675 |
| Latin | 3.165 | 2.408 |
| Italian | 2.931 | 2.259 |
| Middle High German | 2.734 | 1.702 |

So current normalization does **not** turn internal Voynich strings into ordinary natural-language word structure.

At the same time, between-unit dependency becomes stronger after normalization.

This supports a layered picture:

- **internal unit encoding remains highly constrained/cipher-like**;
- **inter-unit grammar becomes more visible as surface variation is removed**.

---

## 11. Prefix/remainder lattices

A major structure appears in families such as:

- `OKA / OTA`
- `OKY / OTY`
- `OKAI / OTAI`
- `OKAII / OTAII`
- `OKEDY / OTEDY`
- `OKEEDY / OTEEDY`
- `OKEEY / OTEEY`
- `OKEO / OTEO`

Contextual cosine examples were very high (often 0.8–0.9).

### Blind cross-corpus lattice search

In matched ~6,000-token windows, requiring at least five attestations per form and at least five shared remainders per prefix pair:

- normalized Voynich: ~**6.3** qualifying prefix-pair lattices; strongest pair ~**10.1** shared remainders
- Naibbe: ~**6.9** lattices; strongest ~**11.0**
- Latin: essentially **0**
- Italian: **0**
- MHG: **0**

`OK/OT` was the top pair in every Voynich window and most Naibbe windows.

**Important caveat:** Naibbe was deliberately designed to reproduce Voynich-style structure, so this is a generative-family comparison, not an independent proof.

---

## 12. Naibbe answer key changes the interpretation of `OK/OT`

Because Naibbe cipher tokens align one-to-one with known plaintext units before the artificial space deletion, its `OK/OT` lattice can be directly decoded.

High-frequency examples:

- `okaiin / otaiin -> t`
- `okain / otain -> u`
- `okeedy / oteedy -> r`
- `okeey / oteey -> s`
- `okar / otar -> m`
- `okal / otal -> l`
- `oky / oty -> p`
- `okchdy / otchdy -> b`
- `okchy / otchy -> g`
- `okchey / otchey -> f`
- `okey / otey -> v`
- `okor / otor -> x`

Among all 32 attested Naibbe `OK+X / OT+X` type pairs:

- only 43.8% of pair *types* map to the same plaintext unit;
- frequency-weighted, **84.8%** of the pair mass maps to the same plaintext unit.

So in a known verbose homophonic cipher, “same remainder under `OK/OT`” is frequently a **literal homophone pair**, though low-frequency exceptions encode related but different plaintext units.

This makes a homophony interpretation a serious candidate for analogous Voynich lattices.

---

## 13. Voynich `OK/OT` is not pure homophony

A calibrated test was developed using Naibbe:

- if `OK/OT` forms are true homophones, after conditioning on the shared remainder, prefix choice should carry almost no extra information about neighbour context;
- if they encode distinct plaintext states, context can distinguish them.

### Naibbe calibration

True-homophone `OK/OT` pairs:

- essentially zero residual neighbour-context MI after conditioning on remainder.

Different-plaintext `OK/OT` pairs:

- right-context excess ~**0.031 bits**
- permutation **p ≈ 0.0033**

### Voynich

Across well-sampled `OK/OT` remainders:

- right-context excess ~**0.038 bits**
- permutation **p ≈ 0.012**

Therefore the entire `OK/OT` distinction cannot simply be erased as homophony.

### Remainder-by-remainder mixture

Strong contrast:

- `OKO / OTO`: excess next-context information ~**0.145 bits**, **p ≈ 0.001**

No detectable residual context under current data for several others, including candidates such as:

- `OKCHO / OTCHO`
- `OKCHY / OTCHY`
- `OKEO / OTEO`
- `OKSHO / OTSHO`

These are **candidate equivalence/homophone classes**, not proven ones.

The best model is now a **mixture**:

- some same-remainder surface forms may be alternative encodings of one hidden state;
- others preserve a real distinction.

---

## 14. Contextual homophone recovery on Naibbe

To calibrate distributional clustering, Naibbe plaintext labels were hidden and frequent ciphertext types were compared only by left/right context.

For sufficiently frequent cipher types:

- same-plaintext pairs median cosine ≈ **0.964**
- different-plaintext pairs median cosine ≈ **0.921**
- AUC for same-plaintext vs different ≈ **0.748**

For a cipher token with at least one frequent homophone:

- nearest neighbour is a true homophone: **32.9%**
- at least one homophone in top five: **47.4%**

Conclusion:

- context is genuinely informative about hidden equivalence classes;
- context alone is far too weak to decode;
- structural factors (shared remainder, prefix family, terminal, boundary state) must be combined with context.

---

## 15. Currier A/B result

Both Currier A and B independently show the same broad mechanisms.

Terminal↔next-unit stem-conditioned excess MI:

- A: ~**+0.028 bits**, p≈0.0033
- B: ~**+0.078 bits**, p≈0.0033

Both independently regenerate substantial `OK/OT × remainder` lattices with many of the same remainder families.

This favours:

> same broad representational machinery, different state distributions

rather than two entirely unrelated ciphers.

However, **Currier language and scribal hand are strongly confounded** in ZL3b:

- A / Hand 1: 112 pages
- B / Hand 2: 46
- B / Hand 3: 28
- B / Hand 5: 7
- A / Hand 3: only 2

Therefore do **not** claim that A/B differences are definitively linguistic rather than scribal/content/cipher-table differences.

---

## 16. f3r-specific interpretation after corrections

Original first line:

`tsheos qopal chol cthol daimg`

Earlier tempting “plant-name” interpretations mostly collapsed under the structural model.

Current approximate factorization:

`T·SHEOS   Q·OPA·L   CHO·L   CTHO·L   DAI·M·G`

Interpretation of factors remains unknown.

Important corrections:

- `tsheos` plausibly contains a paragraph/entry-start gallows-like `t` over an independently attested `sheos` base.
- `qopal` belongs to a recurring `OPA(L/R/...)` family; it is not unique to f3r.
- `chol` and `cthol` are highly recurrent structural families.
- `daimg` likely relates to attested `daim`; final `g` is heavily line-final and may be an appended boundary operation in at least some cases.

Thus **do not use f3r line 1 as a direct plant-name crib**.

First-token uniqueness across 95 Herbal-A/Hand-1 pages:

- raw surface: ~**87.4%** unique
- after latent normalization / conservative gallows handling: ~**70–72%** unique

Entry starts are still unusually novel, but a large chunk of the raw novelty is encoding/morphology.

---

## 17. Failed / demoted hypotheses to preserve

Do not restart these without new evidence:

1. **Simple monoalphabetic substitution to Latin.** Fails transfer and semantic validation.
2. **Homophonic LM optimization as a direct decoder.** Can overfit n-gram statistics with nonsense.
3. **`r ≈ l ≈ m`.** Wrong; `r/l` preserve real information.
4. **`m` only exists as a line-final allograph.** Too simple; internal `m` often belongs to the same terminal paradigm.
5. **Strip all apparent prefixes.** Wrong; some initial material is lexical/structural and not detachable.
6. **`q` is definitely its own latent token.** Too strong. It behaves operator-like morphologically, while segmentation often favours larger `qo...` units.
7. **`CHOM` / `CHAM` as f3r content words.** Artefact of incomplete `m` normalization.
8. **f3r ↔ f54r botanical/topic cluster.** Disappeared after correcting internal `m` normalization.
9. **`OPA` as f3r plant name.** Recurs widely and does not form a convincing botanical cluster.
10. **`OK/OT` wholesale collapse.** Wrong; `OKO/OTO` clearly preserves context information.
11. **In-sample high-order token n-gram gains as evidence.** Sparse and misleading; held-out naive trigram models overfit.

---

## 18. Current latent generative model

A useful current abstraction is:

```text
underlying hidden state Z_i
        ↓
(surface family / prefix-class, remainder/core, terminal state)
        ↓
context-sensitive terminal realization
        ↓
optional concatenation with neighbouring latent units
        ↓
line/paragraph-boundary surface transforms (m/g/gallows-like effects)
        ↓
observed EVA token stream
```

More formally, a latent unit should retain factorized information:

`U_i = (outer-class, remainder/core, terminal, boundary-state)`

Do **not** strip the terminal from the final hidden representation. Terminal stripping is useful only as an exploratory family-discovery transform.

Several surface tuples may later be inferred as emissions of one deeper hidden `Z_i`, but equivalence must be learned rather than assumed.

---

## 19. Most promising next experiment

The next attack should be **latent equivalence-class recovery**, calibrated on Naibbe before touching Voynich semantics.

### Positive-control task on Naibbe

Known target:

`Z_i = plaintext unigram/bigram unit`

Available observed features per cipher token:

- prefix family
- remainder family
- terminal glyph/state
- token frequency
- left/right context distributions
- line/position features if useful
- edit / slot similarity

Goal:

1. Train **no plaintext dictionary**.
2. Infer whether two ciphertext types belong to the same hidden class.
3. Score against Naibbe’s known plaintext-equivalence labels.
4. Cross-validate by holding out ciphertext types, lines, or plaintext classes.
5. Freeze the model/hyperparameters.
6. Apply unchanged to Voynich.

Context alone gives Naibbe same-plaintext AUC ~0.75. A factor-aware method should aim substantially higher before being trusted on Voynich.

### Candidate modelling approaches

Recommended order:

1. **Pairwise probabilistic classifier** for “same hidden state?” using only structural features.
2. Constrained clustering / correlation clustering from pairwise probabilities.
3. Bayesian latent-class model or stochastic block model over context distributions.
4. Only after this works on Naibbe, align inferred Voynich latent states to candidate plaintext-language models.

Do not start with an LLM or semantic embedding. The next problem is still cryptanalytic state recovery, not translation.

---

## 20. Longer-term language/cipher discrimination

Once a candidate Voynich latent-state inventory exists, compare its transition grammar against:

- medieval/late-medieval Latin
- early Italian / Romance
- Middle High German
- other plausible regional languages if justified
- Naibbe plaintext and ciphertext layers
- structured self-citation/generative nulls

Use **held-out cross-entropy** or Bayesian model evidence, not in-sample n-gram fit.

Important target tests:

- Does a single fixed latent mapping generalize across withheld folios?
- Does it generalize across Currier A/B while allowing state-frequency differences?
- Do labels/illustrations gain predictive power *only after* the mapping is fixed?
- Can it explain line-position effects without bespoke per-page rules?
- Is the decoder reversible enough to regenerate the observed surface distributions?

A real solution must explain more than one page.

---

## 21. Reproduction / handoff files

See the `code/` directory:

- `fetch_data.py` — downloads the external corpora used in the experiments.
- `voynich_core.py` — parser, EVA glyph handling, mutual information, permutation tests, segmentation helpers.
- `01_terminal_sandhi.py` — terminal families, line-final `m`, next-unit sandhi test.
- `02_latent_segmenter.py` — held-out segmentation benchmark and f3r Viterbi segmentation.
- `03_lattice_analysis.py` — `OK/OT` and general prefix/remainder lattice analysis.
- `04_naibbe_positive_control.py` — aligns Naibbe pre/post-respacing ciphertext and evaluates the same segmenter against exact deleted-space ground truth; also reports `OK/OT` plaintext mappings.
- `05_equivalence_frontier.py` — starter script for the next frontier: build pairwise structural/context features for latent equivalence-class recovery.
- `requirements.txt`

`results/results_snapshot.json` contains the headline numerical results from the exploratory session so new runs can be checked for parser/version drift.

---

## 22. Source / literature links used repeatedly

These are the main starting points rather than a complete bibliography.

- Zandbergen Voynich transcription overview: `https://www.voynich.nu/transcr.html`
- Currier material: `https://www.voynich.com/currier1.htm`
- Reddy & Knight 2011: `https://aclanthology.org/W11-1511/`
- Hauer & Kondrak TACL: `https://transacl.org/ojs/index.php/tacl/article/view/821`
- Montemurro & Zanette, long-range structure: PLOS One 2013
- Bowern & Lindemann review: Annual Review of Linguistics
- Greshko / Naibbe cipher: `https://www.tandfonline.com/doi/full/10.1080/01611194.2025.2566408`
- Naibbe code/data: `https://github.com/greshko/naibbe-cipher`
- 2026 positional-entropy work: `https://www.tandfonline.com/doi/full/10.1080/01611194.2026.2697318`
- 2026 computational structural analysis used as an independent comparison: `https://github.com/Workwrite-Niidome/voynich-manuscript-analysis`

---

## 23. Epistemic guardrails for continuation

Please preserve these constraints in Codex:

- **Do not call any latent unit a word, letter, morpheme, plant name, or phoneme unless an independent test supports it.**
- Report exploratory p-values as exploratory when the statistic was chosen after observing the pattern.
- Prefer page-/folio-held-out evaluation over random token splits.
- Keep scribal hand, Currier variety, section, and physical line position in the metadata.
- Use multiple transcriptions eventually; a result dependent on EVA/ZL3b editorial decisions is weaker.
- Use Naibbe as a **positive control**, not as proof that Voynich uses the Naibbe cipher.
- Always compare any proposed semantic mapping against structured nulls and blind held-out folios.
- Preserve uncertainty rather than replacing `m` with a single deterministic terminal.
- Do not erase `r/l/n` information in the final latent state merely because stripped families are useful for exploratory clustering.

---

## 24. Best current one-sentence hypothesis

> **The Voynich manuscript most plausibly encodes meaningful information through a layered, context-sensitive, highly compositional surface system with homophonic/near-homophonic variation, latent unit boundaries not identical to written spaces, and strong physical-line transformations; our current methods appear to recover pieces of that encoding layer, but not yet plaintext semantics.**

