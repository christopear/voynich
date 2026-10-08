# Voynich research laboratory

Reproducible structural analysis and experimental cipher recovery for the
Voynich Manuscript. Ciphertext and Latin/Italian source language are working
hypotheses for the current programme, not established decipherment claims.

## Setup

Use Python 3.14 and [uv](https://docs.astral.sh/uv/). From this checkout:

```bash
uv sync --locked
uv run voynich list
uv run python -m unittest discover -s tests -t . -v
```

`uv sync` installs `voynich` from `src/` in editable mode. There is no need to
change `PYTHONPATH` or run Python inside the source directory. `pyproject.toml`
defines dependencies and `uv.lock` fixes their versions.

## Layout

```text
src/voynich/                 Reusable parsers, models and analysis utilities
  acquisition/              Explicit data-download commands
  experiments/              Numbered, runnable research stages
  decipher_search/           Key search, language scoring and synthetic controls
tests/                      Unit, scientific-regression and package tests
docs/                       Research constitution, priorities and framework guide
  protocols/                Historical experiment specifications
  reports/                  Findings, reviews and literature notes
  archive/                  Original handoff material
  guides/                   Development and experiment instructions
data/                       Input corpora and attributed third-party references
results/                    Curated outputs, manifests and research evidence
  overnight/                Historical execution logs
scripts/                    Explicit multi-stage batch runners
```

One package keeps shared parsers, models and corpora together. Input datasets and
historical results are external to the distributable Python wheel.

## Running research

```bash
# List stages without executing analyses.
uv run voynich list
uv run voynich-decipher --help
uv run voynich experiment 12 --help

# Small, separate synthetic control run.
uv run voynich-decipher controls \
  --train data/latin_alfonsi.txt --language latin --family glyph \
  --words 100 --steps 2000 --restarts 4 --workers 2 \
  --output results/scratch/latin_controls.json
```

Numbered analyses can be expensive and may overwrite historical output paths
when explicitly run. Consult the [experiment guide](docs/guides/EXPERIMENTS.md)
first. Batch runners in `scripts/` are not part of setup or the test suite.

## References

- [Architecture decisions and implementation sequence](docs/ARCHITECTURE.md)
- [PostgreSQL connection setup](docs/guides/POSTGRESQL.md)
- [Research constitution](docs/RESEARCH_CONSTITUTION.md)
- [Ranked operation families](docs/OPERATION_FAMILY_PRIORITIES.md)
- [Decipherment framework](docs/DECIPHERMENT_FRAMEWORK.md)
- [Object-oriented cipher API](docs/guides/CIPHER_API.md)
- [Recovery pilot results](results/decipher_framework_2026-09-30/SUMMARY.md)
- [Documentation index](docs/README.md)
- [Development workflow](docs/guides/DEVELOPMENT.md)
- [Migration notes](docs/guides/REPOSITORY_LAYOUT.md)

This folder already has Git history. Use `git diff` to review and `git add -A`
to stage intended file moves together with updates; do not reinitialize it.

## Synthetic cipher laboratory

The [8 October operating report](results/laboratory_2026-10-08/report.html)
contains completed Latin, Italian and Ancient Greek experiments, inspectable
plaintext/ciphertext examples, controls and limitations. Its
[evidence export](results/laboratory_2026-10-08/evidence.json) preserves run IDs,
metrics, source hashes and selected candidates.

See [the operating guide](docs/guides/LABORATORY.md) for fixture APIs, PostgreSQL
registry setup, reproducible search, and the frozen first benchmark plan.
Use `uv run --locked voynich-benchmark preflight configs/benchmarks/initial.json`
to validate readiness without executing encryption or recovery.
