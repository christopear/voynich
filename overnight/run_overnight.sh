#!/usr/bin/env bash
# Overnight batch: coupling-aware test v2 (COUPLING_TEST_V2_PROTOCOL.md) and a
# cross-machine reproducibility check of stages 13, 15 and 16.
# Usage:  ./overnight/run_overnight.sh            (all cores)
#         WORKERS=12 ./overnight/run_overnight.sh (limit parallelism)
set -uo pipefail
cd "$(dirname "$0")/.."
LOG=overnight/logs
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
  echo "kernel:  $(uname -srm)"
  free -g | head -2
} > "$STATUS"

step() { echo "[$(date -Is)] $*" | tee -a "$STATUS"; }

step "uv sync"
uv sync --locked > "$LOG/01_sync.log" 2>&1 || { step "FAILED: uv sync (see 01_sync.log)"; exit 1; }

step "unit tests"
uv run --locked python -m unittest discover -s code -p 'test_*.py' > "$LOG/02_tests.log" 2>&1 \
  || { step "FAILED: unit tests (see 02_tests.log)"; exit 1; }

step "job A: coupling-aware test v2 (17_coupling_test_v2.py)"
uv run --locked python code/17_coupling_test_v2.py --workers "$WORKERS" > "$LOG/10_coupling_v2.log" 2>&1
step "job A exit code: $?"

step "job B: reproducibility reruns of 13, 15, 16 (in parallel, single-threaded each)"
pids=()
for s in 13_equivalence_classes 15_coupled_cipher_transfer 16_coupling_aware_test; do
  uv run --locked python "code/$s.py" > "$LOG/20_$s.log" 2>&1 &
  pids+=("$!:$s")
done
for entry in "${pids[@]}"; do
  pid=${entry%%:*}; name=${entry#*:}
  wait "$pid"; step "job B $name exit code: $?"
done

step "job B: comparing regenerated outputs with committed versions"
DIRS="results/equivalence_2026-09-25 results/coupled_cipher_2026-09-25 results/coupling_test_2026-09-25"
REPORT="$LOG/30_reproducibility.txt"
{
  echo "Files that differ from the committed versions (empty = byte-identical):"
  git status --porcelain -- $DIRS
  echo
  git diff --stat -- $DIRS
} > "$REPORT"
# Keep copies of any differing files for inspection, then restore the committed versions
# so that only job A results and logs are committed.
mkdir -p "$LOG/repro_changed"
git diff --name-only -- $DIRS | while read -r f; do
  cp "$f" "$LOG/repro_changed/$(echo "$f" | tr '/' '__')"
done
git checkout -- $DIRS

step "done: $(date -Is)"
echo
echo "Finished. Please run:"
echo "  git add results/coupling_test_v2_2026-09-25 overnight/logs"
echo "  git commit -m 'Overnight run: coupling test v2 and reproducibility check'"
echo "  git push"
