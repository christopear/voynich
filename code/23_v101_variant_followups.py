"""v101 follow-ups (V101_FOLLOWUP_PROTOCOL.md, items 2a and 2b).

2a: which variant set carries the within-word ending information seen in the
    FULL arm's base model (ADD / ADD-SHAM / DROP one set at a time, 08 design).
2b: variant-test power at the real minority rates of y, k and r.

Run: OPENBLAS_NUM_THREADS=1 uv run --locked python code/23_v101_variant_followups.py [2a] [2b] [--workers 4]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import v101_data as vd

ROOT = vd.ROOT
OUT = ROOT / "results/v101_followup_2026-09-26"
CODE = Path(__file__).resolve().parent
SEED = 20260926
SETS = ("d", "sh", "r", "y", "k", "p", "f", "cph")
LOWRATE = {"y": (15747, 360 / 15747), "k": (8929, 71 / 8929), "r": (5847, (81 + 44 + 25) / 5847)}
CAL_BASES = ("o", "a", "c", "1", "e")
CAL_SEEDS = (1, 2, 3, 4)


def load_module(name, file):
    spec = importlib.util.spec_from_file_location(name, CODE / file)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# 2a
# ---------------------------------------------------------------------------

W = {}


def init_2a():
    p21 = load_module("p21", "21_v101_ports.py")
    lines, mapping = vd.load_corpus()
    p21.FULL_LINES = lines
    eva = vd.eva_of(mapping)
    table = mapping["collapse_table"]
    rows_full = p21.coupling_rows(lines, eva, table, "units")
    W.update(p21=p21, lines=lines, mapping=mapping, eva=eva, table=table,
             families=p21.f.assign_folds(r["family"] for r in rows_full))


def class_groups(table, eva):
    """Set name -> symbols whose EVA class belongs to it; 'other' = remaining multi-member classes."""
    members = defaultdict(set)
    for c, canon in table.items():
        members[canon].add(c)
    groups = defaultdict(set)
    for canon, ms in members.items():
        if len(ms) < 2:
            continue
        cls = eva[canon]
        groups[cls if cls in SETS else "other"] |= ms
    return dict(groups)


def arm_lines(spec):
    kind, name, seed = spec
    lines, table, eva = W["lines"], W["table"], W["eva"]
    if kind == "FULL":
        return lines
    if kind == "COLLAPSED":
        return vd.represent(lines, table)
    group = class_groups(table, eva)[name]
    if kind == "DROP":
        return vd.represent(lines, {c: (table[c] if c in group else c) for c in table})
    add = vd.represent(lines, {c: (c if c in group else table[c]) for c in table})
    if kind == "ADD":
        return add
    return vd.sham_lines(add, table, seed)  # only S has more than one symbol per class here


def job_2a(spec):
    p21 = W["p21"]
    rows = p21.coupling_rows(arm_lines(spec), W["eva"], W["table"], "units")
    pred = p21.run_crossed(rows, "family", W["families"], list)
    return spec, {r["id"]: (r["loss0"], r["loss1"], r["folio"], r["currier"]) for r in pred}


def ci(values, clusters, reps=2000):
    values = np.asarray(values, float)
    ids = sorted(set(clusters)); idx = {c: i for i, c in enumerate(ids)}
    k = np.array([idx[c] for c in clusters])
    s = np.bincount(k, weights=values, minlength=len(ids)); n = np.bincount(k, minlength=len(ids))
    d = np.random.default_rng(SEED).integers(len(ids), size=(reps, len(ids)))
    est = s[d].sum(1) / np.maximum(n[d].sum(1), 1)
    return {"mean": float(values.mean()), "ci": [float(x) for x in np.quantile(est, [0.025, 0.975])]}


def run_2a(workers):
    init_2a()
    groups = class_groups(W["table"], W["eva"])
    specs = [("FULL", None, 0), ("COLLAPSED", None, 0)]
    for s in list(SETS) + ["other"]:
        specs += [("ADD", s, 0), ("DROP", s, 0)] + [("ADDSHAM", s, k) for k in (1, 2, 3)]
    with Pool(workers, initializer=init_2a) as pool:
        res = {}
        for spec, pred in pool.imap_unordered(job_2a, specs):
            res[spec] = pred
            print("2a done", spec, flush=True)
    ids = sorted(res[("FULL", None, 0)])
    folio = [res[("FULL", None, 0)][i][2] for i in ids]
    cur = [res[("FULL", None, 0)][i][3] for i in ids]
    base = {k: np.array([v[i][0] for i in ids]) for k, v in res.items()}
    gain = {k: np.array([v[i][0] - v[i][1] for i in ids]) for k, v in res.items()}
    out = {"groups": {k: sorted(v) for k, v in groups.items()}, "n": len(ids), "sets": {}}
    for subset in ("all", "B"):
        m = np.array([subset == "all" or c == "B" for c in cur])
        fo = [x for x, keep in zip(folio, m) if keep]
        ref = {"base_collapsed_minus_full": ci(base[("COLLAPSED", None, 0)][m] - base[("FULL", None, 0)][m], fo)}
        out.setdefault("reference", {})[subset] = ref
        for s in list(SETS) + ["other"]:
            sham_b = np.mean([base[("ADDSHAM", s, k)] for k in (1, 2, 3)], axis=0)
            sham_g = np.mean([gain[("ADDSHAM", s, k)] for k in (1, 2, 3)], axis=0)
            add_vs_sham = ci(sham_b[m] - base[("ADD", s, 0)][m], fo)
            drop_vs_full = ci(base[("DROP", s, 0)][m] - base[("FULL", None, 0)][m], fo)
            d = {"base_addsham_minus_add": add_vs_sham, "base_drop_minus_full": drop_vs_full,
                 "base_collapsed_minus_add": ci(base[("COLLAPSED", None, 0)][m] - base[("ADD", s, 0)][m], fo),
                 "gain_add_minus_addsham": ci(gain[("ADD", s, 0)][m] - sham_g[m], fo),
                 "gain_full_minus_drop": ci(gain[("FULL", None, 0)][m] - gain[("DROP", s, 0)][m], fo)}
            d["carries_ending_information"] = add_vs_sham["ci"][0] > 0 and drop_vs_full["ci"][0] > 0
            out["sets"].setdefault(s, {})[subset] = d
    return out


# ---------------------------------------------------------------------------
# 2b
# ---------------------------------------------------------------------------

V = {}


def init_2b():
    vt = load_module("vt", "20_v101_variant_test.py")
    lines, mapping = vd.load_corpus()
    coll = vd.represent(lines, mapping["collapse_table"])
    V.update(vt=vt, rows={b: vt.occurrences(lines, coll, None, {b}) for b in CAL_BASES})


def labels_lowrate(vt, rows, control, rate, seed):
    rng = random.Random(seed * 104729 + ("NULL", "STRICT", "RATIO").index(control))
    keys = [vt.res_key(r, "collapsed") for r in rows]
    if control == "NULL":
        return np.array([int(rng.random() < rate) for _ in rows])
    if control == "STRICT":
        count = defaultdict(int)
        for k in keys:
            count[k] += 1
        order = sorted(count); rng.shuffle(order)
        chosen, acc, target = set(), 0, rate / 0.9 * len(rows)
        for k in order:
            if acc >= target:
                break
            chosen.add(k); acc += count[k]
        return np.array([int(k in chosen and rng.random() < 0.9) for k in keys])
    q_lo = rate / (0.25 * 12 + 0.75); q_hi = 12 * q_lo
    prop = {}
    out = []
    for k in keys:
        if k not in prop:
            prop[k] = q_hi if rng.random() < 0.25 else q_lo
        out.append(int(rng.random() < prop[k]))
    return np.array(out)


def job_2b(args):
    target, control, base, seed = args
    vt = V["vt"]
    n, rate = LOWRATE[target]
    rows = V["rows"][base]
    sub = rows if len(rows) <= n else random.Random(1000 * seed + n).sample(rows, n)
    y = labels_lowrate(vt, sub, control, rate, seed)
    if y.sum() < 2:
        return dict(target=target, control=control, base=base, seed=seed, n=len(sub), minority=float(y.mean()),
                    letter_like=False, degenerate=True)
    res, _ = vt.evaluate(sub, y, 2, "collapsed")
    return dict(target=target, control=control, base=base, seed=seed, n=len(sub), minority=float(y.mean()),
                letter_like=res["label"]["letter_like"], R=res["R"], R_w=res["R_w"], degenerate=False)


def run_2b(workers):
    jobs = [(t, c, b, s) for t in LOWRATE for c in ("NULL", "STRICT", "RATIO") for b in CAL_BASES for s in CAL_SEEDS]
    with Pool(workers, initializer=init_2b) as pool:
        reps = []
        for i, r in enumerate(pool.imap_unordered(job_2b, jobs)):
            reps.append(r)
            if (i + 1) % 20 == 0:
                print(f"2b {i + 1}/{len(jobs)}", flush=True)
    reps.sort(key=lambda r: (r["target"], r["control"], r["base"], r["seed"]))
    out = {"replicates": reps, "sets": {}}
    for t, (n, rate) in LOWRATE.items():
        rate_of = lambda c: float(np.mean([r["letter_like"] for r in reps if r["target"] == t and r["control"] == c]))
        d = {"n": n, "minority_rate": rate, "letter_like_rate": {c: rate_of(c) for c in ("NULL", "STRICT", "RATIO")},
             "mean_minority_realised": {c: float(np.mean([r["minority"] for r in reps if r["target"] == t and r["control"] == c]))
                                        for c in ("NULL", "STRICT", "RATIO")}}
        d["size_ok"] = d["letter_like_rate"]["NULL"] <= 0.10
        d["verdict"] = ("not interpretable" if not d["size_ok"] else
                        "not letter-like stands (powered at own rate)" if d["letter_like_rate"]["STRICT"] >= 0.80 else
                        "underpowered")
        out["sets"][t] = d
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("parts", nargs="*", default=["2a", "2b"])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"protocol": "V101_FOLLOWUP_PROTOCOL.md", "seed": SEED,
                "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [ROOT / "V101_FOLLOWUP_PROTOCOL.md", Path(__file__).resolve(), vd.OUT / "mapping.json"]}}
    if "2b" in args.parts:
        r = run_2b(args.workers)
        (OUT / "variant_power_lowrate.json").write_text(json.dumps({"manifest": manifest, **r}, indent=1))
        print(json.dumps(r["sets"], indent=1), flush=True)
    if "2a" in args.parts:
        r = run_2a(args.workers)
        (OUT / "variant_ending_sets.json").write_text(json.dumps({"manifest": manifest, **r}, indent=1))
        print(json.dumps({s: {k: v["all"][k] for k in ("base_addsham_minus_add", "base_drop_minus_full", "carries_ending_information")}
                          for s, v in r["sets"].items()}, indent=1))


if __name__ == "__main__":
    main()
