# Runs on the user's machine

These are CPU jobs. **No GPU is used**: each corpus is about 35,000 tokens, too
small for a GPU to help. Memory use is well under 16 GB.

## Current: coupling-aware test, version 3 (`run_v3.sh`)

Specification: `COUPLING_TEST_V3_PROTOCOL.md`, committed before the code.

This version cross-fits the neighbour classes: they are learned on other pages
than the ones being tested. That fixes the leak found in version 2. It also adds
a leakage gate (B0) and makes the pooled calibration subsets member-disjoint.

* **Calibration:** 3 arms × 2 regimes × 10 seeds = 60 tasks on the labelled
  shared-core cipher.
* **Voynich:** ZL3b and Takahashi IT2a.
* **Output:** `results/coupling_test_v3_2026-09-26/`, with logs in
  `overnight/logs_v3/`.

```bash
cd voynich
git checkout claude/gifted-wright-ctbvn0 && git pull
tmux new -s voynich            # optional, so a closed terminal doesn't stop it
./overnight/run_v3.sh          # uses all cores (fixed since the last run)
```

**Expected duration:** about 20–40 minutes on your 20-thread machine. That is
extrapolated from version 2, which took 3 h 09 min on a single worker with 80
tasks. On one worker it would take about 2.5–3 hours.

Afterwards:

```bash
git add results/coupling_test_v3_2026-09-26 overnight/logs_v3
git commit -m "Run coupling test v3"
git push
```

If something fails, `overnight/logs_v3/00_status.txt` names the step and its log
file. Please push the logs anyway.

## Previous: version 2 and reproducibility check (`run_overnight.sh`, done)

This ran on 25–26 September 2026; see `COUPLING_TEST_V2_FINDINGS_2026-09-26.md`.
Its outputs are in `results/coupling_test_v2_2026-09-25/` and `overnight/logs/`.
It does not need to be run again.

### One-time setup (already done on your machine)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.local/bin/env
git clone https://github.com/christopear/voynich.git
```
