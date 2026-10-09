# Experiment commands

The project uses uv with Python 3.14. Run these commands from the project root:

```bash
uv sync --locked
./scripts/run_baseline.sh
```

To run the boundary experiment against the downloaded transcription:

```bash
uv run --locked python -m voynich.boundary data/ZL3b-n.txt
```

`uv run` uses `.venv` automatically; manual activation is unnecessary.
`pyproject.toml` declares dependencies and `uv.lock` records resolved versions.
The existing `requirements.txt` is retained for the original handoff workflow.
The original scripts use `requests`; the frontier experiments additionally use
NumPy, SciPy and scikit-learn, all recorded in `uv.lock`.
`scripts/run_baseline.sh` downloads the source corpora before running the analyses, so it
requires network access.

The scripts intentionally favour readability and reproducibility over performance.
They recreate the core experimental logic from the exploratory ChatGPT session,
not every scratch calculation.

Important: `conservative_normalizer()` destroys information and exists only for
family/lattice discovery. Do not use its output as the final hidden plaintext
state.

The new combined generalization/layout experiments preserve the earlier scripts
and outputs. Their prospective specification is `docs/protocols/FRONTIER_PROTOCOL.md`.

```bash
uv sync --locked
uv run --locked python -m voynich.acquisition.fetch_frontier_coordinates
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e06_boundary_frontier
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e07_boundary_robustness
uv run --locked python -m unittest discover -s tests -t . -p 'test_boundary_frontier.py' -v
```

`06` writes the primary experiment and individual held-out predictions to
`results/frontier_2026-09-24/`. `07` adds explicitly exploratory checks without
changing the primary results. See `docs/reports/FRONTIER_FINDINGS_2026-09-24.md` for findings,
scope, attribution and limitations. Coordinate input provenance is recorded in
`data/frontier/README.md`. The coordinate fetch requires network access only when
files are missing; model fitting and tests use local inputs.

The next stage tests spelling-family/transcription robustness and compares
specified generative mechanisms. Its protocol is `docs/protocols/MECHANISM_PROTOCOL.md` and
findings are in `docs/reports/MECHANISM_FINDINGS_2026-09-24.md`. Inputs and attribution are in
`data/mechanisms/README.md`; outputs are separate from the frontier results.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e08_robustness_gate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e09_mechanism_benchmark
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e10_recovery_sensitivity
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e11_mixture_controls
uv run --locked python -m unittest discover -s tests -t . -p 'test_*.py' -v
```

`12_reconstruct_claims.py` recomputes the handoff claims whose original drivers
were lost (rare-form decomposition, spaced alternations, split-vs-unsplit,
information trajectory, entropy, lattices, OK/OT context tests, Naibbe
homophone recovery and others). The claim definitions live in
`reconstruction.py`; outputs go to `results/reconstruction_2026-09-25/`, and
the findings are in `docs/reports/RECONSTRUCTION_FINDINGS_2026-09-25.md`. It runs in about
30 seconds and is the last step of `scripts/run_baseline.sh`.

```bash
uv run --locked python -m voynich.experiments.e12_reconstruct_claims
uv run --locked python -m unittest discover -s tests -t . -p 'test_reconstruction.py' -v
```

`parse_zl3b(..., fix_alternatives=True)` corrects the tokeniser's handling of
non-plain alternative readings such as `dai[{cto}:@194;]y`. The default keeps
the original behaviour so earlier results stay reproducible; the effect of the
fix on the parser-dependent claims is saved in `parser_sensitivity.json`.

The §19 equivalence-class stage follows `docs/protocols/EQUIVALENCE_PROTOCOL.md`. `13` is
prospective and `14` is post hoc. Outputs go to `results/equivalence_2026-09-25/`
and the findings are in `docs/reports/EQUIVALENCE_FINDINGS_2026-09-25.md`.

```bash
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e13_equivalence_classes
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e14_equivalence_posthoc
uv run --locked python -m unittest discover -s tests -t . -p 'test_equivalence.py' -v
```

`15_coupled_cipher_transfer.py` tests the frozen §19 classifier on a labelled
non-Naibbe cipher (`slot_cipher.py`), with and without Voynich-style edge
coupling. It follows `docs/protocols/COUPLED_CIPHER_PROTOCOL.md` and writes to
`results/coupled_cipher_2026-09-25/`.

```bash
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e15_coupled_cipher_transfer
uv run --locked python -m unittest discover -s tests -t . -p 'test_slot_cipher.py' -v
```

`16_coupling_aware_test.py` runs the coupling-aware terminal-alternation test
(`coupling_test.py`), calibrated on a shared-core slot cipher. It follows
`docs/protocols/COUPLING_TEST_PROTOCOL.md`, writes to `results/coupling_test_2026-09-25/`, and
takes about 2 hours.

```bash
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e16_coupling_aware_test
uv run --locked python -m unittest discover -s tests -t . -p 'test_coupling_test.py' -v
```

`17_coupling_test_v2.py` (`coupling_test_v2.py`) is version 2 of the
coupling-aware test. It is CPU-parallel and follows
`docs/protocols/COUPLING_TEST_V2_PROTOCOL.md`. The overnight batch, which also runs a
cross-machine reproducibility check of 13, 15 and 16, is launched with
`./scripts/run_overnight.sh`; see `docs/guides/OVERNIGHT.md`.

`18_coupling_test_v3.py` (`coupling_test_v3.py`) is version 3 of the test: the
same design as version 2, but with neighbour classes cross-fitted across page
folds. It follows `docs/protocols/COUPLING_TEST_V3_PROTOCOL.md` and is launched with
`./scripts/run_v3.sh`.

`08` and `09` are prospective tests for this stage. `10` and `11` are explicitly
post-result sensitivities. `mechanism_models.py` implements all three generators
and their diagnostics. The encoder is an independently weighted, invertible
adaptation using published Naibbe tables, not the published card-deck algorithm.
## v101 transcription and cipher-family stages (19–25)

These stages were dropped by the October layout migration and restored on
9 October 2026. Claude reports the completed reproduction check in commit
`10bce4c` (9 October), rerun in a clean copy of the
checkout and compared with `scripts/compare_results.py` (provenance fields
ignored). Every regenerated output is identical to the committed file:
v101 mapping, variant calibration, variant test and post hoc rates (19–20);
the three ports (21; one citation string differs only because the docs moved);
gain decomposition, spacing and locality post hoc analyses, and low-rate power
(22–23), including per-set ending effects (23, part 2a); and all cipher-family
step A and step B outputs (24–25). Protocols
and findings are `docs/protocols/V101_PROTOCOL.md`,
`docs/protocols/V101_FOLLOWUP_PROTOCOL.md`,
`docs/protocols/CIPHER_FAMILY_PROTOCOL.md` and the matching
`docs/reports/*_FINDINGS_2026-09-26.md`.

`v101.py` parses Glen Claston's latin-1 v101 file and infers the v101 → EVA
mapping by EM alignment against ZL3b. `v101_data.py` builds the full, collapsed
and sham representations used by the paired tests. `cipher_families.py` holds
the cipher-family generators, layout modifier and alphabet-independent
fingerprints.

```bash
uv run --locked python -m voynich.experiments.e19_v101_mapping                            # ~3 min
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e20_v101_variant_test --workers 4   # ~10 min
uv run --locked python -m voynich.experiments.posthoc_e20_v101_variant_rates              # post hoc tables
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e21_v101_ports       # ~30 min
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e22_v101_gain_decomposition --workers 4
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.posthoc_e22_v101_spacing
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e23_v101_variant_followups 2b 2a --workers 4
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.posthoc_e23_v101_locality
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e24_cipher_family_benchmark --workers 4   # ~15 min
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e25_homophone_recovery                    # ~20 min
```

These commands write to the historical result directories. To rerun without
touching committed results, run them in a full copy of the checkout, and
compare with `scripts/compare_results.py`:

```bash
git archive HEAD | tar -x -C /path/to/copy && cd /path/to/copy && uv sync --locked
OPENBLAS_NUM_THREADS=1 uv run --locked python -m voynich.experiments.e24_cipher_family_benchmark --workers 4
uv run --locked python /path/to/checkout/scripts/compare_results.py \
  results/cipher_families_2026-09-26 /path/to/checkout/results/cipher_families_2026-09-26
```

Pointing `VOYNICH_ROOT` at a copy of `data/` and `results/` alone is not
enough. The manifests hash the protocol and the script's own source by their
path under the workspace root, so the code and docs must live in the same
tree.

## Capacity screen (run before any manuscript search)

```bash
uv run --locked python -m voynich.evaluation.capacity --output results/<new-dir>/screen.json
```

This checks whether a decoding family's units can carry plaintext-level
information. See `results/capacity_screen_2026-10-09/README.md` and
`AGENTS.md`.

## Direct decipherment framework

`26_decipherment_search.py` adds bounded key/segmentation search and synthetic
recovery controls. See [the framework guide](../DECIPHERMENT_FRAMEWORK.md)
for commands, model definitions, score limitations and pilot results. It requires
no additional dependencies. It does not run automatically as part of older
experiments.
