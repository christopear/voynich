# Code handoff

The project uses uv with Python 3.14. Run these commands from the project root:

```bash
uv sync --locked
./run_all.sh
```

To run the boundary experiment against the downloaded transcription:

```bash
uv run --locked python code/boundary.py data/ZL3b-n.txt
```

`uv run` uses `.venv` automatically; manual activation is unnecessary.
`pyproject.toml` declares dependencies and `uv.lock` records resolved versions.
The existing `requirements.txt` is retained for the original handoff workflow.
The original scripts use `requests`; the frontier experiments additionally use
NumPy, SciPy and scikit-learn, all recorded in `uv.lock`.
`run_all.sh` downloads the source corpora before running the analyses, so it
requires network access.

The scripts intentionally favour readability and reproducibility over performance.
They recreate the core experimental logic from the exploratory ChatGPT session,
not every scratch calculation.

Important: `conservative_normalizer()` destroys information and exists only for
family/lattice discovery. Do not use its output as the final hidden plaintext
state.

The new combined generalization/layout experiments preserve the earlier scripts
and outputs. Their prospective specification is `FRONTIER_PROTOCOL.md`.

```bash
uv sync --locked
uv run --locked python code/fetch_frontier_coordinates.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/06_boundary_frontier.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/07_boundary_robustness.py
uv run --locked python -m unittest discover -s code -p 'test_boundary_frontier.py' -v
```

`06` writes the primary experiment and individual held-out predictions to
`results/frontier_2026-09-24/`. `07` adds explicitly exploratory checks without
changing the primary results. See `FRONTIER_FINDINGS_2026-09-24.md` for findings,
scope, attribution and limitations. Coordinate input provenance is recorded in
`data/frontier/README.md`. The coordinate fetch requires network access only when
files are missing; model fitting and tests use local inputs.

The next stage tests spelling-family/transcription robustness and compares
specified generative mechanisms. Its protocol is `MECHANISM_PROTOCOL.md` and
findings are in `MECHANISM_FINDINGS_2026-09-24.md`. Inputs and attribution are in
`data/mechanisms/README.md`; outputs are separate from the frontier results.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/08_robustness_gate.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/09_mechanism_benchmark.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/10_recovery_sensitivity.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/11_mixture_controls.py
uv run --locked python -m unittest discover -s code -p 'test_*.py' -v
```

`12_reconstruct_claims.py` recomputes the handoff claims whose original drivers
were lost (rare-form decomposition, spaced alternations, split-vs-unsplit,
information trajectory, entropy, lattices, OK/OT context tests, Naibbe
homophone recovery and others). The claim definitions live in
`reconstruction.py`; outputs go to `results/reconstruction_2026-09-25/`, and
the findings are in `RECONSTRUCTION_FINDINGS_2026-09-25.md`. It runs in about
30 seconds and is the last step of `run_all.sh`.

```bash
uv run --locked python code/12_reconstruct_claims.py
uv run --locked python -m unittest discover -s code -p 'test_reconstruction.py' -v
```

`parse_zl3b(..., fix_alternatives=True)` corrects the tokeniser's handling of
non-plain alternative readings such as `dai[{cto}:@194;]y`. The default keeps
the original behaviour so earlier results stay reproducible; the effect of the
fix on the parser-dependent claims is saved in `parser_sensitivity.json`.

The §19 equivalence-class stage follows `EQUIVALENCE_PROTOCOL.md`. `13` is
prospective and `14` is post hoc. Outputs go to `results/equivalence_2026-09-25/`
and the findings are in `EQUIVALENCE_FINDINGS_2026-09-25.md`.

```bash
OPENBLAS_NUM_THREADS=1 uv run --locked python code/13_equivalence_classes.py
OPENBLAS_NUM_THREADS=1 uv run --locked python code/14_equivalence_posthoc.py
uv run --locked python -m unittest discover -s code -p 'test_equivalence.py' -v
```

`15_coupled_cipher_transfer.py` tests the frozen §19 classifier on a labelled
non-Naibbe cipher (`slot_cipher.py`), with and without Voynich-style edge
coupling. It follows `COUPLED_CIPHER_PROTOCOL.md` and writes to
`results/coupled_cipher_2026-09-25/`.

```bash
OPENBLAS_NUM_THREADS=1 uv run --locked python code/15_coupled_cipher_transfer.py
uv run --locked python -m unittest discover -s code -p 'test_slot_cipher.py' -v
```

`16_coupling_aware_test.py` runs the coupling-aware terminal-alternation test
(`coupling_test.py`), calibrated on a shared-core slot cipher. It follows
`COUPLING_TEST_PROTOCOL.md`, writes to `results/coupling_test_2026-09-25/`, and
takes about 2 hours.

```bash
OPENBLAS_NUM_THREADS=1 uv run --locked python code/16_coupling_aware_test.py
uv run --locked python -m unittest discover -s code -p 'test_coupling_test.py' -v
```

`17_coupling_test_v2.py` (`coupling_test_v2.py`) is version 2 of the
coupling-aware test. It is CPU-parallel and follows
`COUPLING_TEST_V2_PROTOCOL.md`. The overnight batch, which also runs a
cross-machine reproducibility check of 13, 15 and 16, is launched with
`./overnight/run_overnight.sh`; see `overnight/README.md`.

`18_coupling_test_v3.py` (`coupling_test_v3.py`) is version 3 of the test: the
same design as version 2, but with neighbour classes cross-fitted across page
folds. It follows `COUPLING_TEST_V3_PROTOCOL.md` and is launched with
`./overnight/run_v3.sh`.

`08` and `09` are prospective tests for this stage. `10` and `11` are explicitly
post-result sensitivities. `mechanism_models.py` implements all three generators
and their diagnostics. The encoder is an independently weighted, invertible
adaptation using published Naibbe tables, not the published card-deck algorithm.

The v101 stage follows `V101_PROTOCOL.md`; findings are in
`V101_FINDINGS_2026-09-26.md` and outputs in `results/v101_2026-09-26/`.
`v101.py` parses Glen Claston's latin-1 v101 file and infers the v101 → EVA
mapping by EM alignment against ZL3b; `v101_data.py` builds the full, collapsed
and sham representations used by the paired tests.

```bash
uv run --locked python code/19_v101_mapping.py                         # ~3 min
OPENBLAS_NUM_THREADS=1 uv run --locked python code/20_v101_variant_test.py --workers 4   # ~10 min
uv run --locked python code/20b_v101_variant_posthoc.py                # post hoc tables
OPENBLAS_NUM_THREADS=1 uv run --locked python code/21_v101_ports.py    # ~30 min
uv run --locked python -m unittest discover -s code -p 'test_v101.py' -v
```
