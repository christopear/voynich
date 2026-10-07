# Literature notes: Parisel, antenore toolkit, voynich-collective

25 September 2026. These were read before designing the coupled-cipher test
(`COUPLED_CIPHER_PROTOCOL.md`). Access limits are stated where they apply.

## Parisel (2026), arXiv:2604.19762

*Evidence of Layered Positional and Directional Constraints in the Voynich
Manuscript: Implications for Cipher-Like Structure.* Version 2 is dated
16 June 2026.

**Access.** This environment's network policy blocks arXiv, Kaggle and the
mirrors (Bytez, Pith, awesomepapers). The paper text itself was **not read**. What
follows comes from:

* search-result abstracts;
* the author's public support repository,
  <https://github.com/labyrinthinesecurity/currier-signatures>, commit
  `5d50101b57957bc7feaa002cec01d1ce5b2b11d9`, which is read in full and run
  locally (it has no license file, so none of its code is copied here);
* the independent audit in voynich-collective (below).

**Claims, per the abstract:**

* Word-internal glyph sequences are right-to-left optimized, while word-boundary
  dependence runs left to right. None of the comparison languages (English,
  French, Hebrew, Arabic) shows this dissociation.
* Neither a parametric slot generator nor a Cardan grille (Rugg) reproduces all
  four signatures jointly across its tested parameters.
* Naibbe was also tested as a cipher generator.
* The signatures are offered as benchmarks any generative or cryptanalytic model
  must clear.

**The four signatures, as implemented in `signatures_v27.py`** (EVA greedy
tokenizer, lines as sentences):

1. **E→S%.** Each glyph is classed "start" if it is at least twice as frequent
   word-initially as word-finally, or "end" in the reverse case. E→S% is the
   share of word boundaries where an end-class glyph is followed by a start-class
   glyph. Reference values: Currier A 71.0%, Currier B 64.3%. Pass: reference
   ±15 points.
2. **Bilateral extremity.** At least one glyph has a start:end ratio above 100:1,
   and at least one the reverse.
3. **Boundary MI.** *Raw* (not shuffle-corrected) mutual information between a
   word's last glyph and the next word's first glyph. Reference: A 0.586, B 0.498
   bits. Pass: at least half the reference.
4. **Shape.** The distribution of word-initial glyphs must be Zipfian or
   intermediate, not flat.

The pass bands are generous. The repo's README shows a submitted generator
passing all four signatures for Currier A. The signatures concern word edges
only, not homophony or vocabulary.

**Our run of Parisel's verifier on Greshko's Naibbe ciphertext**
(`naibbe_cipher_respaced.txt`, `--fast`, applying the same one-line
`signatures_v26 → v27` import repair that voynich-collective documented):

| Signature | Naibbe | Currier A reference | Currier B reference |
|---|---:|---:|---:|
| E→S% | 52.1 | 71.0 (**fail**) | 64.3 (pass) |
| Bilateral | yes | pass | pass |
| Boundary MI (bits) | 0.221 | 0.586 (**fail**) | 0.498 (**fail**) |
| Shape | intermediate | pass | pass |
| Signatures passed | | 2/4 | 3/4 |

Naibbe's weakest point against Voynich is cross-word edge coupling.

## antenore/voynich-toolkit

<https://github.com/antenore/voynich-toolkit>, commit `cb13763`, 30 April 2026,
MIT license. Read: the README, the paper abstract, and the homophone and Naibbe
modules.

* **Main thesis:** a monoalphabetic EVA→Hebrew mapping. The author reports a
  lexical signal at 3–4-letter words that collapses at 5+ letters. Grammatical
  prefixes fail 0/7, and the text is still unreadable. An LLM-generated
  "known-plaintext crib attack" is part of the evidence. We treat that design as
  weak: generated cribs encoded through the proposed cipher cannot validate the
  cipher.
* **Useful structural replications,** with permutation z-scores:
  * `m` as a line-end glyph (z = +55.5);
  * lines as self-contained units;
  * simple gallows marking paragraph starts, while split gallows do not;
  * Montemurro–Zanette section-specific vocabulary confirmed, but their
    illustration-linkage prediction not confirmed;
  * a Rugg grille reproduces 10 of 16 properties.
* **Homophones:** homophone detection works on *single characters*, using
  context-similarity and anti-co-occurrence heuristics. It has no labelled
  validation.
* **Overlap with our work:** none on word-level equivalence classes.

## voynich-collective (SoylentAquamarine)

<https://github.com/SoylentAquamarine/voynich-collective>, read at its
25 September 2026 state (`knowledge-base/state.md`, the Cardan audit report and
the preregistration). A multi-agent project (Claude lead, ChatGPT auditor) with
preregistered mechanism controls. It overlaps substantially with our
`MECHANISM_*` stage and goes further.

* **Profile and Naibbe.** They use a six-criterion joint profile: character
  entropy H1/H2, learned-unit BPE scale, token-order share, held-out edge
  prediction, and hapax share.
  * Naibbe passes entropy, unit scale and order.
  * It fails edge prediction (≈0 bits against Voynich's +0.187) and hapax (41%
    against 70%).
* **Other named mechanisms.** Parisel's frozen Cardan grille fails 5 of 6
  criteria. Timm–Schinner self-citation fails, with edge gain ≈0.
* **Constructed nulls.** Three engineered mechanisms now pass all six criteria:
  * `boundary-shift-v2`;
  * `coupling-v2`, which is Naibbe plus a coupling that copies the previous
    token's last glyph plus resegmentation;
  * `coupling-v3.1`.

  The project concludes that the joint profile cannot, by itself, identify a real
  generating process.
* **Historical motivation.** A literature review proposes sandhi (e.g. Tamil
  glide insertion) as a linguistic motivation for edge coupling. No mechanism
  implements it yet.
* **Homophones:** no homophone-class or equivalence-class recovery was found.

## What this means for our next step

* **Where the sources agree.** Parisel's MI signature, voynich-collective's
  held-out edge criterion and our terminal↔next-initial result all make the same
  point: cross-word edge coupling is what separates Voynich from Naibbe and from
  the other published generators.
* **Why that matters for our classifier.** If homophone choice depends on the
  neighbouring word, true homophones get *different* contexts. The §19
  classifier relies mainly on context similarity, so it would miss them or
  split them. That could explain the `chol/chor`-type conflicts.
* **Therefore:** the next test needs a labelled, non-Naibbe cipher, tuned to
  Voynich statistics including edge coupling, and run with and without
  context-conditioned homophone choice.
* **Novelty:** labelled homophone-class recovery appears to be new relative to
  these three sources.
