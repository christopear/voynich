#!/usr/bin/env bash
# Reproduce the original baseline. This downloads inputs and rewrites its outputs.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p results
uv run --locked python -m voynich.acquisition.fetch_data
uv run --locked voynich experiment 01 > results/01_terminal_sandhi.json
uv run --locked voynich experiment 02 > results/02_latent_segmenter.json
uv run --locked voynich experiment 03 > results/03_lattice_analysis.json
uv run --locked voynich experiment 04 > results/04_naibbe_positive_control.json
uv run --locked voynich experiment 05
uv run --locked voynich experiment 12
