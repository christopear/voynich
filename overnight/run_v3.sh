#!/usr/bin/env bash
# Coupling-aware test, version 3 (cross-fitted classes). See COUPLING_TEST_V3_PROTOCOL.md.
# Usage:  ./overnight/run_v3.sh            (all cores)
#         WORKERS=12 ./overnight/run_v3.sh (limit parallelism)
set -uo pipefail
cd "$(dirname "$0")/.."
LOG=overnight/logs_v3
mkdir -p "$LOG"
# Decide the worker count BEFORE limiting BLAS threads: nproc obeys OMP_NUM_THREADS.
WORKERS=${WORKERS:-$(nproc --all)}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
STATUS="$LOG/00_status.txt"

{
  echo "start:   $(date -Is)"
  echo "host:    $(hostname)  cpus: $(nproc --all)  workers: $WORKERS"
  echo "commit:  $(git rev-parse HEAD)  branch: $(git rev-parse --abbrev-ref HEAD)"
  echo "uv:      $(uv --version 2>&1)"
} > "$STATUS"
step() { echo "[$(date -Is)] $*" | tee -a "$STATUS"; }

step "uv sync"
uv sync --locked > "$LOG/01_sync.log" 2>&1 || { step "FAILED: uv sync (see 01_sync.log)"; exit 1; }
step "unit tests"
uv run --locked python -m unittest discover -s code -p 'test_*.py' > "$LOG/02_tests.log" 2>&1 \
  || { step "FAILED: unit tests (see 02_tests.log)"; exit 1; }
step "coupling-aware test v3 (18_coupling_test_v3.py), workers=$WORKERS"
uv run --locked python code/18_coupling_test_v3.py --workers "$WORKERS" > "$LOG/10_coupling_v3.log" 2>&1
step "exit code: $?"
step "done"
echo
echo "Finished. Please run:"
echo "  git add results/coupling_test_v3_2026-09-26 overnight/logs_v3"
echo "  git commit -m 'Run coupling test v3'"
echo "  git push"
