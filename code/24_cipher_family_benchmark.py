"""Step A of CIPHER_FAMILY_PROTOCOL.md: which families can reproduce the Voynich fingerprints?

Run: OPENBLAS_NUM_THREADS=1 uv run --locked python code/24_cipher_family_benchmark.py [--workers 4]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
from collections import defaultdict
from pathlib import Path

import numpy as np

import cipher_families as cf
import mechanism_models as mm
import v101_data as vd

ROOT = cf.ROOT
OUT = ROOT / "results/cipher_families_2026-09-26"
SEEDS = (1, 2, 3, 4, 5, 6)
HELD_OUT = (101, 102)
Z_MAX = 3.0
BOOT = 200

W = {}


def setup():
    w1, w2, train = cf.currier_b_windows()
    W.update(windows={"W1": w1, "W2": w2}, training=mm.Training(train))


def run(job):
    config, window, seed = job
    laid, _ = cf.simulate(config, W["windows"][window], seed, W["training"])
    if laid is None:
        return dict(key=cf.config_key(config), window=window, seed=seed, not_run=True)
    units = "eva" if config["family"] in cf.EVA_UNIT_FAMILIES else "char"
    return dict(key=cf.config_key(config), family=config["family"], layout=config["layout"], language=config["language"],
                params=config["params"], window=window, seed=seed, not_run=False, **cf.fingerprint(laid, units))


def targets():
    """Voynich targets: ZL3b W1/W2, IT2a and v101 on the same pages."""
    w1, w2, _ = cf.currier_b_windows()
    pages = {"W1": {ln["page"] for ln in w1}, "W2": {ln["page"] for ln in w2}}
    it = cf.frontier.load_lines(ROOT / "data/mechanisms/IT2a-n.txt")
    vlines, _ = vd.load_corpus()
    out = {}
    for win, lines in (("W1", w1), ("W2", w2)):
        out[f"ZL_{win}"] = (win, lines, "eva")
        out[f"IT_{win}"] = (win, [ln for ln in it if ln["page"] in pages[win]], "eva")
        out[f"v101_{win}"] = (win, [dict(page=ln["page"], words=ln["words"], gaps=ln["gaps"],
                                         paragraph_start=ln["paragraph_start"]) for ln in vlines if ln["page"] in pages[win]],
                              "char")
    return out


def config_stats(runs, window):
    """key -> (mean vector, sd vector) over the main seeds; family per key."""
    by = defaultdict(list)
    for r in runs:
        if r["window"] == window and not r["not_run"] and r["seed"] in SEEDS:
            by[r["key"]].append([r[k] for k in cf.PRIMARY])
    stats = {k: (np.mean(v, axis=0), np.std(v, axis=0, ddof=1)) for k, v in by.items()}
    fam = {r["key"]: r["family"] for r in runs if not r["not_run"]}
    return stats, fam


def evaluate(vec, sd_v, stats, fam, families=None):
    """Per family: compatible?, best config, its |z| per fingerprint; plus L0-only compatibility."""
    res = {}
    for key, (mu, sd) in stats.items():
        f = fam[key]
        if families and f not in families:
            continue
        z = (vec - mu) / np.sqrt(sd ** 2 + sd_v ** 2)
        worst = float(np.max(np.abs(z)))
        d = res.setdefault(f, dict(compatible=False, compatible_L0=False, best_key=None, best_worst=np.inf,
                                   best_z=None, n_compatible_configs=0))
        if worst <= Z_MAX:
            d["compatible"] = True; d["n_compatible_configs"] += 1
            if key.endswith("|L0"):
                d["compatible_L0"] = True
        if worst < d["best_worst"]:
            d.update(best_key=key, best_worst=worst, best_z=dict(zip(cf.PRIMARY, map(float, z))))
    for d in res.values():
        d["binding"] = [k for k, v in d["best_z"].items() if abs(v) > Z_MAX]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    configs = list(cf.configurations())
    jobs = [(c, w, s) for c in configs for w in ("W1", "W2") for s in SEEDS + HELD_OUT]
    with multiprocessing.get_context("fork").Pool(args.workers) as pool:
        runs = []
        for i, r in enumerate(pool.imap_unordered(run, jobs, chunksize=4)):
            runs.append(r)
            if (i + 1) % 200 == 0:
                print(f"runs {i + 1}/{len(jobs)}", flush=True)
    runs.sort(key=lambda r: (r["key"], r["window"], r["seed"]))
    (OUT / "step_a_runs.json").write_text(json.dumps(runs, indent=0, ensure_ascii=False))
    not_run = sorted({r["key"] for r in runs if r["not_run"]})

    # Voynich targets and bootstrap SDs.
    tg = targets()
    tvals, tsd = {}, {}
    for name, (win, lines, units) in tg.items():
        fp = cf.fingerprint(lines, units)
        boot = cf.page_bootstrap(lines, BOOT, 20260926, units)
        tvals[name] = fp
        tsd[name] = {k: float(np.std([b[k] for b in boot], ddof=1)) for k in cf.PRIMARY + cf.SECONDARY}
        print("target", name, {k: round(fp[k], 4) for k in cf.PRIMARY}, flush=True)

    verdicts = {}
    stats = {w: config_stats(runs, w) for w in ("W1", "W2")}
    for name, (win, _, _) in tg.items():
        vec = np.array([tvals[name][k] for k in cf.PRIMARY]); sdv = np.array([tsd[name][k] for k in cf.PRIMARY])
        verdicts[name] = evaluate(vec, sdv, *stats[win])
    robust = {}
    for f in cf.FAMILIES:
        a, b = verdicts["ZL_W1"][f]["compatible"], verdicts["ZL_W2"][f]["compatible"]
        robust[f] = ("compatible" if a and b else "excluded" if not a and not b else "window-dependent (undecided)")

    # Gates: self-consistency (G1) and discrimination (G2) on W1 with ZL W1 sampling SD.
    sdv = np.array([tsd["ZL_W1"][k] for k in cf.PRIMARY])
    st, fam = stats["W1"]
    g1 = defaultdict(list); g2 = defaultdict(lambda: defaultdict(list))
    for r in runs:
        if r["window"] != "W1" or r["not_run"] or r["seed"] not in HELD_OUT:
            continue
        ev = evaluate(np.array([r[k] for k in cf.PRIMARY]), sdv, st, fam)
        g1[r["family"]].append(ev[r["family"]]["compatible"])
        for other, d in ev.items():
            g2[r["family"]][other].append(d["compatible"])
    gates = {"G1_self_consistency": {f: {"rate": float(np.mean(v)), "n": len(v), "pass": float(np.mean(v)) >= 0.90}
                                     for f, v in g1.items()},
             "G2_cross_compatibility": {f: {o: float(np.mean(v)) for o, v in d.items()} for f, d in g2.items()}}
    conf = []
    for a in cf.FAMILIES:
        for b in cf.FAMILIES:
            if a < b and a in g2 and b in g2 and gates["G2_cross_compatibility"][a].get(b, 0) >= 0.5 \
                    and gates["G2_cross_compatibility"][b].get(a, 0) >= 0.5:
                conf.append([a, b])
    gates["confusable_pairs"] = conf

    for name in verdicts:
        for f, d in verdicts[name].items():
            d["best_worst"] = float(d["best_worst"])
    summary = {"robust_ZL": robust,
               "by_target": {name: {f: ("compatible" if d["compatible"] else "excluded")
                                    + (" (only with layout rule L1)" if d["compatible"] and not d["compatible_L0"] else "")
                                    for f, d in v.items()} for name, v in verdicts.items()},
               "interpretable": {f: gates["G1_self_consistency"].get(f, {}).get("pass", False) for f in cf.FAMILIES},
               "not_run_configs": not_run}
    for f in cf.FAMILIES:
        zl = [verdicts[f"{t}_{w}"][f]["compatible"] for t in ("IT", "v101") for w in ("W1", "W2")]
        summary.setdefault("transcription_sensitive", {})[f] = any(
            verdicts[f"{t}_{w}"][f]["compatible"] != verdicts[f"ZL_{w}"][f]["compatible"] for t in ("IT", "v101") for w in ("W1", "W2"))
    (OUT / "step_a_verdicts.json").write_text(json.dumps(
        {"summary": summary, "targets": tvals, "target_bootstrap_sd": tsd, "verdicts": verdicts}, indent=1, ensure_ascii=False))
    (OUT / "step_a_gates.json").write_text(json.dumps(gates, indent=1))
    (OUT / "step_a_manifest.json").write_text(json.dumps({
        "protocol": "CIPHER_FAMILY_PROTOCOL.md", "seeds": SEEDS, "held_out": HELD_OUT, "z_max": Z_MAX, "bootstrap": BOOT,
        "window_pages": {w: sorted({ln["page"] for ln in W["windows"][w]}) for w in W["windows"]},
        "window_slots": {w: cf.slots(W["windows"][w]) for w in W["windows"]},
        "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [
            ROOT / "CIPHER_FAMILY_PROTOCOL.md", Path(__file__).resolve(), ROOT / "code/cipher_families.py",
            ROOT / "data/ZL3b-n.txt", ROOT / "data/latin_alfonsi.txt", ROOT / "data/italian_dante.txt", ROOT / "data/mhg_fh.txt"]}},
        indent=1))
    print(json.dumps(summary, indent=1)); print(json.dumps(gates["G1_self_consistency"], indent=1))


if __name__ == "__main__":
    main()
