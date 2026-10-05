# Layout migration — 5 October 2026

This migration reorganizes the current working tree into one installable Python
package, preserving previous uncommitted framework work. It does not switch
branches, merge upstream research, commit or push. At migration time this
checkout was 11 commits behind its fetched tracking branch; those changes are
separate from this refactor. Use the path map when coordinating that merge.

| Former location | Current location |
|---|---|
| `code/` shared modules | `src/voynich/` |
| `code/01_*.py` … | `src/voynich/experiments/e01_*.py` … |
| `code/decipher_search/` | `src/voynich/decipher_search/` |
| `code/fetch_*.py` | `src/voynich/acquisition/` |
| `code/test_*.py` | `tests/` |
| Root protocols | `docs/protocols/` |
| Root findings/reviews | `docs/reports/` |
| Original handoff/kickoff | `docs/archive/` |
| `code/README.md` | `docs/guides/EXPERIMENTS.md` |
| `run_all.sh` | `scripts/run_baseline.sh` |
| `overnight/run_*.sh` | `scripts/run_*.sh` |
| Overnight outputs/logs | `results/overnight/` |

See the full [migration map](../migration_paths.json). Historical documents,
datasets and scientific result contents are unchanged. Their recorded paths
and hashes intentionally remain historical facts. New runs use new paths/hashes;
current guides and runnable scripts are updated.

Implementation changes concern packaging, imports, workspace discovery,
import-safe experiment entry points and runner commands. File-based dynamic
imports became normal package imports. The old overnight runner no longer
automatically discards regenerated results.

The distribution name remains `voynich-codex-handoff`; its Python import name
is `voynich`. The uv project changes from virtual to editable, with third-party
dependency versions unchanged.

Replace old `python code/...` commands with `uv run voynich experiment NN` or
`uv run python -m voynich.experiments.eNN_name`. Direct decipherment uses
`uv run voynich-decipher`. Data acquisition is explicit through
`python -m voynich.acquisition.fetch_data` or `fetch_frontier_coordinates`.
