# Codex kickoff prompt

Use the following as the first instruction in Codex after opening this folder:

---

We are continuing a research-oriented attempt to understand the Voynich Manuscript. Read `CONTINUATION.md` completely before changing code. Then inspect `results/results_snapshot.json` and all files under `code/`.

First tasks:

1. Create a Python virtual environment and install `requirements.txt`.
2. Run `code/fetch_data.py` and then `run_all.sh`.
3. Compare the reproduced results with `results/results_snapshot.json`; investigate material deviations before proceeding. Do not silently tune parsers or thresholds to recover expected values.
4. Refactor the exploratory code into a tested research package while preserving the original calculations as regression tests.
5. Implement the next-frontier experiment described in section 19 of `CONTINUATION.md`: latent equivalence-class recovery calibrated on Naibbe.

For the Naibbe positive control, build ciphertext-only pair features including at minimum:

- context-distribution similarity;
- same/different prefix family;
- same remainder after factorization;
- terminal relationship;
- EVA-glyph edit structure;
- frequency and frequency ratio;
- positional / boundary statistics where useful.

Target label for Naibbe only: whether two ciphertext types map to the same known plaintext unit. Use grouped cross-validation so closely related ciphertext forms or the same plaintext class cannot trivially leak across train/test. Report ROC-AUC, PR-AUC, precision/recall at useful operating points, calibration, and ablations.

Do not use plaintext content as a feature. The plaintext answer key is only the evaluation label.

Once the model/hyperparameters are frozen, apply the exact same ciphertext-only model to Voynich. Produce a ranked set of candidate hidden equivalence classes, but do NOT assign semantic meanings yet.

Maintain these epistemic constraints:

- EVA words are not assumed to be plaintext words.
- EVA characters are not assumed to be plaintext letters.
- `r/l/n/m` information must be retained in the final latent representation even when terminal-stripped forms are used for family discovery.
- `OK/OT` must not be wholesale merged: `OKO/OTO` has a strong measured context distinction.
- Treat Naibbe as a positive control / existence proof, not as the Voynich solution.
- Use folio-held-out or grouped evaluation wherever possible.
- Any claimed advance must survive a control/null and should be tested on more than one transcription before being treated as robust.

The research goal is to move from surface-statistical structure toward a falsifiable latent-state decipherment model, not to generate attractive translations.

---
