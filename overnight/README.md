# Overnight run

Two CPU jobs. **No GPU is used**: every corpus here is about 35,000 tokens, so a
GPU would not speed anything up. The run scales with CPU cores, and memory use is
modest (well under 16 GB).

* **Job A: coupling-aware test, version 2.**
  * Specification: `COUPLING_TEST_V2_PROTOCOL.md`, committed before any real run.
  * Calibration: 4 arms × 2 regimes × 10 seeds = 80 tasks on the labelled
    shared-core cipher.
  * Then Voynich ZL3b and Takahashi IT2a.
  * Writes `results/coupling_test_v2_2026-09-25/`.
* **Job B: cross-machine reproducibility.**
  * Reruns stages 13, 15 and 16 and reports whether their outputs are
    byte-identical to the committed ones.
  * Differing files are copied into `overnight/logs/repro_changed/`, and the
    committed originals are then restored automatically.

## One-time setup (Ubuntu)

```bash
# 1. uv (manages Python 3.14 and the locked dependencies); skip if installed
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env        # or open a new shell

# 2. the repository, on the working branch
git clone https://github.com/christopear/voynich.git   # or: cd voynich && git fetch
cd voynich
git checkout claude/gifted-wright-ctbvn0
git pull
```

All data files are in the repository. Network access is needed only for `uv`
to download Python and the pinned packages on first use.

## Run

Use `tmux` or `nohup` so the run survives a closed terminal, and disable
suspend for the night:

```bash
tmux new -s voynich
./overnight/run_overnight.sh              # uses all cores
# or: WORKERS=12 ./overnight/run_overnight.sh
```

Detach with `Ctrl-b d` and reattach with `tmux attach -t voynich`. Progress is
logged in `overnight/logs/00_status.txt` and `overnight/logs/10_coupling_v2.log`.

**Expected duration.** This is an estimate from the version 1 run, whose tasks
were the same size and took 15–20 minutes each on one core. It was not measured
on your machine.

| Part | Time |
|---|---|
| Job A calibration (80 tasks) | about 20–27 CPU-hours: ~1.5–2 h on 16 threads, 3–4 h on 8, 6–7 h on 4 |
| Job A Voynich (runs alongside calibration) | ~20–40 min |
| Job B (13, 15 and 16 in parallel; 16 is the slow one) | ~2 h after job A |

**Total:** about 4–6 hours on a typical 8–16-thread desktop.

## Afterwards

```bash
git add results/coupling_test_v2_2026-09-25 overnight/logs
git commit -m "Overnight run: coupling test v2 and reproducibility check"
git push
```

Then tell Claude the push is done. If anything fails, `overnight/logs/00_status.txt`
names the failing step and its log file. Please push the logs anyway.
