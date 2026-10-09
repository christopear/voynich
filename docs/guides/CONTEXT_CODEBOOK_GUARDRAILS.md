# Decisions for a contextual word-code study

9 October 2026. Design decisions, **not an executed study or a frozen numerical
protocol**. Read with the constitution and ledger rows 10, 13, 14 and 18.

Stage 29 first tested frequency contributions and Currier A. Its
[report](../../results/frequency_currier_a_2026-10-09/README.md) shows why the next
model must explain common recurring types as well as rare ones. These groups
must not be called function words and content words without independent evidence.

## 1. A small encoder with an explicit reverse mapping

Use disjoint codewords for each plaintext word, initially two alternatives, with
one fixed mapping across all pages. Compare IID choice to bounded persistence
using the **same** codebook and specified marginal choice law. Do not create
new codewords per page or choose page parameters after inspecting fit. Preserve
the normalized plaintext word sequence exactly; state what normalization loses.

Distinguish two persistence mechanisms before choosing either: a single table
preference shared by every word on a page, versus a separately remembered variant
for each encountered word. They have very different state costs and predictions.
A refresh probability controls the latter's reuse; page resets are explicit.
Validate marginal frequencies rather than assuming equal codebook size means
equal realised frequency distributions. Retain source and seed dependence.

## 2. Charge for everything that encodes a choice

If codeword sets are disjoint, the reverse dictionary decodes without knowing
the encoder's current variant. Calling that state *extra secret decoding key*
would be inaccurate. It nevertheless contributes to the generative model:
report state size, initialization, transitions, refresh choices and reset rules.

For k choices, a fixed-width state description costs ceil(log2(k)) bits per
stored choice: one per page for a shared preference, or one per encountered
type per page for per-word persistence. Also record refresh indicators and
new choices. This is an explicit coding convention, not a universal entropy
lower bound. Random trajectories are charged by their declared probability law
(-log2 probability) in predictive/description comparisons; do not double-charge
them as both arbitrary secret keys and sampled trajectories. An arbitrary fitted
trajectory must be paid for explicitly, never hidden behind a PRNG seed.

Charge the codeword grammar, plaintext dictionary and assignment too. For a
fixed ordered set of M codewords assigned in disjoint groups of k to V ordered
plaintext entries (M=kV), the uniform assignment choice alone is
log2(M!/(k!)^V) bits. Dictionary spelling and glyph grammar are additional costs.
If an algorithm supplies the mapping, describe and charge that algorithm and its
parameters rather than claiming both a free arbitrary dictionary and compression.

For C with U=f(C), I(C;P)=I(U;P)+I(C;P|U). Page-dependent choices can add the
second term even without more semantic content. This is why a better page score
does not support meaning. For a decoder requiring state S, retain
H(U)<=H(C)+H(S|C), with the actual sampling and unit alignment specified.

## 3. Build the inside of codewords before interpreting a fit

Construct a bounded prefix/middle/suffix grammar from development glyph strings
only. Freeze the glyph tokenizer, allowable empty slots, lengths, dependencies,
exceptions and selection law before reserved evaluation. A slot boundary need
not be a plaintext morpheme. Count **unique strings** after concatenation, not
slot combinations: multiple slot tuples may collide. Reject dictionaries that
assign the same output to different plaintext entries. Log2 of the unique
support is a maximum distinguishable-symbol capacity, not achieved entropy.

Compare held-out codeword coverage, glyph transition/length distributions,
capacity, word recurrence, frequency-decomposed page association, role effects
and boundary coupling jointly. A huge generated support with low realised
entropy is not automatically informative enough. A free exception dictionary
that memorizes the target defeats this study. Compare both token-weighted and
type-weighted grammar fits; frequent forms must not hide failure on new types.

## 4. R2 is an adversary, not a ceremonial control

Train R2's lexical and glyph distributions on the same development folios used
to fit the slot grammar; exclude evaluation folios from both. Declare their
different parameter counts and tuning budgets. The existing copy generator uses
recent-word windows and mutations, so **shuffling can damage R2 too**. Its
order sensitivity must be measured, not assumed to be zero.

Compare original order, within-page whole-word shuffles, and line-order shuffles
that keep paragraph/line roles. Keep page association intact in these order
controls; a cross-page shuffle tests a different question. Apply identical
controls and evaluator freedom to synthetic ciphers, R2 and the manuscript.
An order statistic is discriminating only if calibrated cipher/R2 distributions
separate and the frozen prediction transfers. Known-key grammar recovery from
a synthetic cipher does not provide a Voynich key or prove a language model.

Freeze all settings on development folios, then score reserved ones without
new glyph lists, fresh exceptions or page-specific tuning. These folios have
been explored previously, so call them reserved for this fit, not untouched.
If both models match, the result is non-identifiability, not cipher support.
If neither matches, revisit the representation rather than expanding the grid.

## 5. Historical and visual evidence remain separate gates

Do not describe a 1,500–4,500-entry codebook as attested around 1420 without a
specific dated key. The [source check](../../data/historical_cipher_sources/README.md)
does not verify that claim. Keep large-key simulations explicitly hypothetical;
report manual lookup, writing and state-update burdens separately from fit.

For cribs, inventory non-zodiac label locus classes and page contexts first.
Do not turn speculative plant identifications in transcription comments into
ground truth. Botanical, pharmaceutical and astronomical labels need independent
glyph-to-image alignment, with image coordinates, alternatives and uncertainty.
Reserve folios and whole lexical types before semantic fitting. Keep the earlier
five-anchor gate intact; cross-domain additions need a new protocol and an
explicit statement of whether one codebook is assumed across those domains.
A person depicted with a star is not automatically the referent of its nearby
text. Five spellings without independently justified referents are not five cribs.

The next execution protocol should be a small calibrated slot/state/R2 comparison
with exact budgets and stopping rules. Do not proceed directly to an unrestricted
word-code key search on the basis of the stage-29 diagnostic.
