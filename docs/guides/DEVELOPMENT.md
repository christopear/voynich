# Development workflow

## Environment and tests

```bash
uv sync --locked
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python -m unittest discover -s tests -t . -v
uv run --locked python -m unittest tests.test_decipher_search -v
uv build
```

The existing suite uses standard-library `unittest`. GitHub Actions runs the
complete local-data suite on changes. Downloads and long experiments are
explicit operations, not CI. Results of the configured remote workflow must be
checked after pushing; local validation does not mean CI has already run.

## Where new work goes

- Reusable logic: `src/voynich/` or a focused subpackage.
- Experiment orchestration: `src/voynich/experiments/eNN_descriptive_name.py`.
  Provide `main()` and a main guard. Importing a module must not download data,
  start an experiment or overwrite results.
- Tests: `tests/test_*.py`, importing through `voynich` rather than file paths.
- Prospective study designs: `docs/protocols/`; dated findings: `docs/reports/`.
- Disposable runs: `results/scratch/`. Curated outputs need settings, seeds,
  input/code hashes and an interpretation note.
- Input provenance and upstream attribution: `data/`. Vendored upstream Python
  files remain reference materials, not application code.

The CLI discovers `eNN_*.py` modules automatically. Existing IDs and gaps are
preserved. No empty application/notebook/config scaffolding is required.

## Data paths and packaging

Use `voynich.paths.ROOT`, `DATA` and `RESULTS` instead of counting parent
directories or assuming a current working directory. Editable installs find
the checkout automatically. For a wheel installed elsewhere, set `VOYNICH_ROOT`
to a research workspace containing `data/` and the needed inputs/results.

`requirements.txt` is an optional pip convenience pointing at this project,
not a second dependency list. Prefer uv with the lockfile for reproducibility.

## Git review

This is already a Git checkout. Review `git status`, `git diff` and, after
staging intended work, `git diff --cached --stat`. Git detects renames from
content when committed. IDE state, caches, environments and scratch results
are ignored; curated evidence remains trackable.

Do not automatically discard regenerated scientific outputs. Review their
differences and metadata before deciding what to commit.
