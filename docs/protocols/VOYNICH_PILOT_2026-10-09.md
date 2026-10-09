# Voynich page search pilot — 9 October 2026

Frozen before execution. Exploratory pilot, not a decipherment or a family exclusion test.

Use ZL3b f26r for search and f31r for frozen-key transfer: both annotated Currier B,
herbal, hand 2. Page choice follows the content/Currier premise and was made before
search scores. These pages are not previously untouched research holdouts. Keep
only plain lowercase EVA words; omit whole ambiguous tokens (including uncertain
comma separators), recording loci and raw tokens. Treat retained spaces as word
spaces, including gaps closed by filtering and line joins. This is a limitation.

Compare raw EVA characters with compound-aware units (cth, ckh, cph, cfh, ch, sh),
using stable reversible symbol labels. Neither is claimed to be the true alphabet.
For each representation compare fixed single-symbol-to-Latin-letter maps with
one or at most two cipher symbols per plaintext letter. No nulls, transposition,
state changes, plaintext pairs, variable segmentation, or lost-space recovery.

For each of 2 representations × 2 capacities × 2 algorithms × 2 seeds × 3 input
conditions, evaluate 4,096 proposals, population 8: 48 runs / 196,608 proposals.
Search seeds 7 and 19. Conditions: original page, shuffled symbols preserving
counts and space positions, shuffled whole words preserving word inventory.
Control seeds are search seed+1000 (development) and +2000 (transfer). Thus there
are only two independent control realizations per representation. Word shuffle
is a deliberately difficult control of order, not of internal word morphology.
Use the existing scorer/strategies without tuning based on Voynich results.

Search model: Celsus, 60,000 normalized characters starting 30% into the source.
Post-selection model: analogous Pliny segment, never used for selection. Frozen
transfer applies the development key without completing unseen symbols; report
coverage and exclude whole unknown-containing words from language scoring,
resetting model context at gaps. Report scored character counts, so incomplete
coverage cannot masquerade as a full-page improvement. Ordinary Latin anchors
use 600-character source slices at 85%, with no searches.

Compare final loss to best of the shared eight initial states; report character
cross-entropy separately from key/choice penalties. Compare original and controls
within the same representation/capacity. Do not rank raw and compound encodings
by bits per input unit, which have different denominators. Compare independent
Latin score and frozen transfer, and inspect all original outputs, not cherry-
picked words. Record mappings and seed stability. A lower optimized score alone
is expected and is not evidence of correct letters. No significance or posterior
probability claims from this small exploratory screen. Natural-looking isolated
words are not translations.

Registry and bounded artifacts use the existing PostgreSQL experiment runner.
Source/environment hashes identify execution even if working-tree changes exist.
Reproduce:

```sh
uv run --env-file .env --locked python -m voynich.laboratory.voynich_pilot \
  --output results/runs/voynich-pilot-2026-10-09
```

Review after this pilot; do not silently broaden searches to chase a Latin-looking
candidate. The next experiment must address whichever assumption/control fails.
