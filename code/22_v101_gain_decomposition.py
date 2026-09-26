"""Why is the 08 coupling gain about twice as large on v101 as on ZL3b? (V101_FOLLOWUP_PROTOCOL.md, item 1)

Builds four corpora on the ZL3b P0 lines that align to v101 text lines by
aligning the two line strings character by character: ZL letters or v101
letters, each combined with ZL spacing or v101 spacing. Runs the 08 family x
folio design on each, and decomposes the Currier B gain difference into
spacing, reading and line-set effects with a shared folio bootstrap.

Run: OPENBLAS_NUM_THREADS=1 uv run --locked python code/22_v101_gain_decomposition.py [--workers 4]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import v101_data as vd

ROOT = vd.ROOT
OUT = ROOT / "results/v101_followup_2026-09-26"
CODE = Path(__file__).resolve().parent
SEED = 20260926
BOOT = 2000
SENTINEL = "#"
SEPS = {".": "ordinary", ",": "uncertain", "|": "drawing"}
SEP_OF = {v: k for k, v in SEPS.items()}


def load_module(name, file):
    spec = importlib.util.spec_from_file_location(name, CODE / file)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


f = load_module("frontier", "06_boundary_frontier.py")
g08 = load_module("gate08", "08_robustness_gate.py")


# ---------------------------------------------------------------------------
# Line strings and character alignment
# ---------------------------------------------------------------------------

def word_chars(w: dict, translit=None) -> str:
    text = w["word"] if translit is None else "".join(translit.get(c, SENTINEL) for c in w["word"])
    return text if w["clean"] else SENTINEL * max(1, len(w["word"]))


def line_string(words, gaps, translit=None) -> str:
    out = word_chars(words[0], translit)
    for g, w in zip(gaps, words[1:]):
        out += SEP_OF[g] + word_chars(w, translit)
    return out


def is_sep(c):
    return c in SEPS


def align_chars(a: str, b: str):
    """Edit alignment; letters never substitute separators. Returns (a_char|None, b_char|None) columns."""
    n, m = len(a), len(b)
    INF = 10 ** 9
    D = [[0] * (m + 1) for _ in range(n + 1)]
    B = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0], B[i][0] = i, 1
    for j in range(1, m + 1):
        D[0][j], B[0][j] = j, 2
    for i in range(1, n + 1):
        x = a[i - 1]; sx = is_sep(x)
        Di, Dp = D[i], D[i - 1]
        for j in range(1, m + 1):
            y = b[j - 1]
            sub = INF if sx != is_sep(y) else (0 if x == y else 1)
            best, k = Dp[j - 1] + sub, 0
            if Dp[j] + 1 < best:
                best, k = Dp[j] + 1, 1
            if Di[j - 1] + 1 < best:
                best, k = Di[j - 1] + 1, 2
            Di[j], B[i][j] = best, k
    cols, i, j = [], n, m
    while i > 0 or j > 0:
        k = B[i][j]
        if k == 0:
            cols.append((a[i - 1], b[j - 1])); i -= 1; j -= 1
        elif k == 1:
            cols.append((a[i - 1], None)); i -= 1
        else:
            cols.append((None, b[j - 1])); j -= 1
    return cols[::-1]


def hybrid(cols, letters: str, spaces: str) -> str:
    """letters/spaces in {'Z','V'}: which side supplies letters and which supplies separators."""
    out = []
    for a, b in cols:
        for side, c in (("Z", a), ("V", b)):
            if c is None:
                continue
            if is_sep(c) and side == spaces:
                out.append(c)
            elif not is_sep(c) and side == letters:
                out.append(c)
    return "".join(out)


def parse_string(s: str):
    parts = re.split(r"([.,|])", s)
    words = [{"word": p, "clean": bool(p) and SENTINEL not in p and bool(re.fullmatch("[a-z]+", p))}
             for p in parts[::2]]
    gaps = [SEPS[p] for p in parts[1::2]]
    return words, gaps


# ---------------------------------------------------------------------------
# 08 design
# ---------------------------------------------------------------------------

def rows_for(lines, folios):
    rows = [r for r in f.observations(lines) if r["kind"] == "ordinary" and r["folio"] in folios]
    for r in rows:
        r["family"] = g08.family(r["stem"])
        r["fold"] = folios[r["folio"]]
    return rows


FAMILY_FOLDS: dict = {}


def run_design(rows):
    out = []
    for fold in range(5):
        for ff in range(5):
            train = [r for r in rows if r["fold"] != fold and FAMILY_FOLDS[r["family"]] != ff]
            test = [r for r in rows if r["fold"] == fold and FAMILY_FOLDS[r["family"]] == ff]
            if not test:
                continue
            base, full = f.Model(train), f.Model(train, context=True)
            out.extend(f.score(test, base.predict(test), full.predict(test), "family_x_folio", fold))
    return out


def job(args):
    name, rows = args
    return name, run_design(rows)


def init(families):
    global FAMILY_FOLDS
    FAMILY_FOLDS = families


# ---------------------------------------------------------------------------

def build():
    """Line pairs, the six corpora's rows, and the shared family folds."""
    gate = json.loads((ROOT / "results/mechanisms_2026-09-24/gate_manifest.json").read_text())
    folios = gate["folios"]
    zl_lines = f.load_lines(ROOT / "data/ZL3b-n.txt")
    zby = {ln["locus"]: ln for ln in zl_lines}

    v_lines, mapping = vd.load_corpus()
    eva = vd.eva_of(mapping)
    vby = {ln["locus"]: ln for ln in v_lines}
    pairs = []
    with (vd.OUT / "line_alignment.csv").open() as fh:
        for r in csv.DictReader(fh):
            if r["zl_descriptor"][1:] == "P0" and r["zl_locus"] in zby and r["v101_locus"] in vby:
                pairs.append((zby[r["zl_locus"]], vby[r["v101_locus"]]))

    corpora = {k: [] for k in ("ZZ", "ZV", "VZ", "VV")}
    r1_same = r1_total = 0
    for zl, vl in pairs:
        zs = line_string(zl["words"], zl["gaps"])
        vs = line_string(vl["words"], vl["gaps"], eva)
        cols = align_chars(zs, vs)
        for key in corpora:
            words, gaps = parse_string(hybrid(cols, key[0], key[1]))
            corpora[key].append(dict(zl, words=words, gaps=gaps))
        zz = corpora["ZZ"][-1]["words"]
        r1_total += len(zl["words"])
        r1_same += sum(a["clean"] == b["clean"] and (not a["clean"] or a["word"] == b["word"])
                       for a, b in zip(zl["words"], zz)) if len(zz) == len(zl["words"]) else 0
    r1 = r1_same / r1_total

    # V-all: every v101 text line as v101-EVA, 06-style line dicts.
    v_all = []
    for ln in v_lines:
        words = [{"word": "".join(eva.get(c, SENTINEL) for c in w["word"]) if w["clean"] else w["word"],
                  "clean": w["clean"]} for w in ln["words"]]
        v_all.append(dict(page=ln["page"], folio=ln["folio"], number=ln["number"], locus=ln["locus"],
                          paragraph_start=ln["paragraph_start"], paragraph_end=ln["paragraph_end"],
                          words=words, gaps=ln["gaps"], meta=ln["meta"]))

    all_rows = {"Z-all": rows_for(zl_lines, folios), "V-all": rows_for(v_all, folios),
                **{k: rows_for(v, folios) for k, v in corpora.items()}}
    fams = dict(gate["families"])
    missing = sorted({r["family"] for rows in all_rows.values() for r in rows} - set(fams))
    fams.update(f.assign_folds(missing) if missing else {})
    return dict(gate=gate, folios=folios, pairs=pairs, eva=eva, all_rows=all_rows, fams=fams,
                missing=missing, r1=r1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    b = build()
    folios, pairs, all_rows, fams, missing, r1 = (b[k] for k in ("folios", "pairs", "all_rows", "fams", "missing", "r1"))
    print({k: len(v) for k, v in all_rows.items()}, "missing families", len(missing), "R1", round(r1, 4), flush=True)

    with Pool(args.workers, initializer=init, initargs=(fams,)) as pool:
        preds = dict(pool.map(job, list(all_rows.items())))

    summ = {}
    for k, p in preds.items():
        summ[k] = {"all": f.summary(p), "B": f.summary([r for r in p if r["currier"] == "B"]),
                   "A": f.summary([r for r in p if r["currier"] == "A"])}
        for s in summ[k].values():
            s.pop("gain_by_fold", None)
        print(k, "B gain", round(summ[k]["B"]["gain_bits"], 5), "base acc", round(summ[k]["B"]["accuracy_base"], 4), flush=True)
    r0 = summ["Z-all"]["B"]
    r0_pass = abs(r0["gain_bits"] - 0.02805) <= 1e-4 and r0["n"] == 8013

    # Shared folio bootstrap.
    fol = sorted(folios)
    fidx = {x: i for i, x in enumerate(fol)}
    draw = np.random.default_rng(SEED).integers(len(fol), size=(BOOT, len(fol)))

    def boot_series(subset):
        out = {}
        for k, p in preds.items():
            rs = [r for r in p if subset is None or r["currier"] == subset]
            s = np.zeros(len(fol)); n = np.zeros(len(fol))
            for r in rs:
                s[fidx[r["folio"]]] += r["loss0"] - r["loss1"]; n[fidx[r["folio"]]] += 1
            out[k] = (s[draw].sum(1) / np.maximum(n[draw].sum(1), 1), s.sum() / n.sum())
        return out

    def stat(name, est, series):
        return {"estimate": float(est), "ci": [float(x) for x in np.quantile(series, [0.025, 0.975])]}

    decomposition = {}
    for label, subset in (("B", "B"), ("all", None)):
        G = boot_series(subset)
        bs = {k: v[0] for k, v in G.items()}; pt = {k: v[1] for k, v in G.items()}
        q = lambda fn: stat("", fn(pt), fn(bs))
        d = {"G": {k: float(v) for k, v in pt.items()},
             "D": q(lambda g: g["VV"] - g["ZZ"]),
             "S": q(lambda g: ((g["ZV"] - g["ZZ"]) + (g["VV"] - g["VZ"])) / 2),
             "R": q(lambda g: ((g["VZ"] - g["ZZ"]) + (g["VV"] - g["ZV"])) / 2),
             "I": q(lambda g: g["VV"] - g["VZ"] - g["ZV"] + g["ZZ"]),
             "L_Z": q(lambda g: g["ZZ"] - g["Z-all"]),
             "L_V": q(lambda g: g["VV"] - g["V-all"]),
             "all_gap": q(lambda g: g["V-all"] - g["Z-all"])}
        D, S, R = d["D"], d["S"], d["R"]
        if D["ci"][0] <= 0 <= D["ci"][1]:
            v = "line-set / observation-set driven"
        else:
            qual = lambda x: np.sign(x["estimate"]) == np.sign(D["estimate"]) and not (x["ci"][0] <= 0 <= x["ci"][1]) \
                and abs(x["estimate"]) >= 0.5 * abs(D["estimate"])
            sq, rq = qual(S), qual(R)
            v = "both" if sq and rq else "spacing-driven" if sq else "reading-driven" if rq else "mixed / interaction"
        d["verdict"] = v
        decomposition[label] = d

    # Secondary: identical observations in ZZ and VV.
    def keyed(p):
        seen = Counter(); out = {}
        for r in sorted(p, key=lambda r: (r["locus"], r["index"])):
            k = (r["locus"], r["left"], r["right"])
            out[k + (seen[k],)] = r; seen[k] += 1
        return out
    kz, kv = keyed(preds["ZZ"]), keyed(preds["VV"])
    common = sorted(set(kz) & set(kv))
    same = {}
    for label, subset in (("B", "B"), ("all", None)):
        ks = [k for k in common if subset is None or kz[k]["currier"] == subset]
        gz = np.array([kz[k]["loss0"] - kz[k]["loss1"] for k in ks]); gv = np.array([kv[k]["loss0"] - kv[k]["loss1"] for k in ks])
        folio_of = [kz[k]["folio"] for k in ks]
        ids = sorted(set(folio_of)); ci_idx = np.array([ids.index(x) for x in folio_of])
        diff = gv - gz
        sd = np.bincount(ci_idx, weights=diff, minlength=len(ids)); nd = np.bincount(ci_idx, minlength=len(ids))
        dr = np.random.default_rng(SEED).integers(len(ids), size=(BOOT, len(ids)))
        est = sd[dr].sum(1) / np.maximum(nd[dr].sum(1), 1)
        same[label] = {"n": len(ks), "share_of_ZZ": len(ks) / sum(1 for r in preds["ZZ"] if subset is None or r["currier"] == subset),
                       "gain_ZZ": float(gz.mean()), "gain_VV": float(gv.mean()),
                       "VV_minus_ZZ": {"estimate": float(diff.mean()), "ci": [float(x) for x in np.quantile(est, [0.025, 0.975])]},
                       "base_acc_ZZ": float(np.mean([kz[k]["correct0"] for k in ks])),
                       "base_acc_VV": float(np.mean([kv[k]["correct0"] for k in ks]))}

    result = {"R0_reproduction": {"gain_B": r0["gain_bits"], "n_B": r0["n"], "pass": bool(r0_pass)},
              "R1_zz_token_identity": {"share": r1, "pass": r1 >= 0.99},
              "line_pairs": len(pairs), "rows": {k: len(v) for k, v in all_rows.items()},
              "summaries": summ, "decomposition": decomposition, "same_observations": same,
              "manifest": {"script": "code/22_v101_gain_decomposition.py", "protocol": "V101_FOLLOWUP_PROTOCOL.md",
                           "seed": SEED, "bootstrap": BOOT, "missing_family_folds": len(missing),
                           "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in [ROOT / "V101_FOLLOWUP_PROTOCOL.md", Path(__file__).resolve(),
                                                vd.OUT / "mapping.json", vd.OUT / "line_alignment.csv"]}}}
    (OUT / "gain_decomposition.json").write_text(json.dumps(result, indent=1))
    print(json.dumps({k: result[k] for k in ("R0_reproduction", "R1_zz_token_identity")}, indent=1))
    print(json.dumps(decomposition, indent=1)); print(json.dumps(same, indent=1))


if __name__ == "__main__":
    main()
