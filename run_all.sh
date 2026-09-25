#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/code"
uv run --locked python fetch_data.py
uv run --locked python 01_terminal_sandhi.py > ../results/01_terminal_sandhi.json
uv run --locked python 02_latent_segmenter.py > ../results/02_latent_segmenter.json
uv run --locked python 03_lattice_analysis.py > ../results/03_lattice_analysis.json
uv run --locked python 04_naibbe_positive_control.py > ../results/04_naibbe_positive_control.json
uv run --locked python 05_equivalence_frontier.py
cd ..
uv run --locked python code/12_reconstruct_claims.py
