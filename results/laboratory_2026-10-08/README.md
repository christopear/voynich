# Operating evidence — 8 October 2026

Open [report.html](report.html) in a browser. It is self-contained; filtering and
expandable examples work without a server. [evidence.json](evidence.json) retains
source provenance, environments, run IDs, metrics, original/audited reachability
labels, plans, baseline restart diagnostics and one selected candidate per run.
Raw bounded search archives remain under ignored `results/runs/` and registrations
remain in the local PostgreSQL database. This export is reviewable without either.

## Reproduction

Use the locked environment and PostgreSQL setup in
[the operating guide](../../docs/guides/LABORATORY.md). Commands refuse existing
output directories. Exact registered repeats require a rerun reason through the
lower-level runner; use a fresh research database to reproduce the complete study
without changing existing registrations. Environment/source fingerprints change
with code revisions, so compare recorded hashes rather than assuming bitwise replay.

```bash
uv run --locked python -m voynich.laboratory.roundtrips --output results/runs/roundtrips-new
uv run --env-file .env --locked voynich-benchmark run configs/benchmarks/initial.json \
  --output results/runs/initial-new --workers 4
uv run --env-file .env --locked python -m voynich.laboratory.focused \
  --plan configs/benchmarks/focused-2026-10-08.json --output results/runs/focused-new
uv run --env-file .env --locked python -m voynich.laboratory.page_recovery --output results/runs/pages-new
uv run --env-file .env --locked python -m voynich.laboratory.shift_recovery --output results/runs/shifts-new
```

Repeat the focused command for the `ablation-2026-10-08.json` and three
`factor-*-2026-10-08.json` plans, each with a distinct output path. The report
exporter accepts those paths as repeated `--ablation` arguments:

```bash
uv run --locked python -m voynich.laboratory.report \
  --roundtrips results/runs/roundtrips-verified-2026-10-08 \
  --baseline results/runs/initial-benchmark-2026-10-08 \
  --focused results/runs/focused-2026-10-08 \
  --pages results/runs/page-recovery-2026-10-08 \
  --shifts results/runs/shift-recovery-2026-10-08 \
  --ablation results/runs/ablation-2026-10-08 \
  --ablation results/runs/factor-600-500-2026-10-08 \
  --ablation results/runs/factor-120-4000-2026-10-08 \
  --ablation results/runs/factor-120-500-2026-10-08 \
  --output results/operating-report-new
```

Replace paths with new runs to export their results. The known-key matrix was
verified twice with identical cases; the second run is the exported matrix,
not an additional independent sample. Its separate registry sidecar records
the aggregate fixture-validation registration.

## Interpretation

This demonstrates synthetic cipher feasibility and bounded solver capabilities.
It does not decipher Voynich, exclude a cipher family, establish language-wide
success rates, or reconstruct a particular historical key. Missing held-out
symbols remain formal failures. Post-search partial diagnostics never modify
the learned key or the original gate. Historical sources and edition licenses
are linked in the report and retained in `data/laboratory_sources/`.
