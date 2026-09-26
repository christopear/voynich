"""Ports of the ending-coupling (06/08), §19 (13) and hidden-boundary analyses to v101.

V101_PROTOCOL.md, Part B. Arms: FULL (v101 symbols), COLLAPSED (v101 with each
symbol replaced by the canonical symbol of its EVA class), SHAM1-3 (variant
labels permuted within each class), plus a descriptive v101-EVA bridge arm.

Run: OPENBLAS_NUM_THREADS=1 uv run --locked python code/21_v101_ports.py [coupling|equivalence|boundary ...]
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, mannwhitneyu, spearmanr

import v101_data as vd

ROOT = vd.ROOT
OUT = vd.OUT
SEED = 20260926
CODE = Path(__file__).resolve().parent


def load_module(name, file):
    spec = importlib.util.spec_from_file_location(name, CODE / file)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


f = load_module("frontier", "06_boundary_frontier.py")
g08 = load_module("gate08", "08_robustness_gate.py")
ORIGINAL_GLYPHS = f.eva_glyphs


def boot_mean_ci(values, clusters, reps=2000, seed=SEED):
    values = np.asarray(values, float); clusters = np.asarray(clusters)
    ids = sorted(set(clusters)); idx = {c: i for i, c in enumerate(ids)}
    ci = np.array([idx[c] for c in clusters])
    s = np.bincount(ci, weights=values, minlength=len(ids)); m = np.bincount(ci, minlength=len(ids))
    draw = np.random.default_rng(seed).integers(len(ids), size=(reps, len(ids)))
    est = s[draw].sum(1) / np.maximum(m[draw].sum(1), 1)
    return {"mean": float(values.mean()), "ci": [float(x) for x in np.quantile(est, [0.025, 0.975])], "n": len(values)}


def verdict(d_coll, d_sham):
    if d_coll["ci"][0] > 0 and d_sham["ci"][0] > 0:
        return "variants carry information"
    if d_coll["ci"][1] < 0 and d_sham["ci"][1] < 0:
        return "variants are noise for this analysis"
    return "no evidence either way"


# ---------------------------------------------------------------------------
# B1. Ending coupling (06 crossed stem x folio; 08 family x folio)
# ---------------------------------------------------------------------------

def coupling_rows(lines, eva, coll_table, mode):
    """Ordinary within-line pairs whose left word ends in an n/l/r-class unit.

    mode 'units': a glyph is one v101 unit (FULL/COLLAPSED/SHAM).
    mode 'eva': words are EVA transliterations with the original glyph rules (bridge arm).
    Ids, targets, families and stem folds are keyed on the full v101 word, so the
    unit arms contain identical observations.
    """
    rows = []
    for ln, full in zip(lines, FULL_LINES):
        for i, kind in enumerate(ln["gaps"]):
            if kind != "ordinary":
                continue
            a, b = ln["words"][i:i + 2]
            fa = full["words"][i]
            if not (a["clean"] and b["clean"]):
                continue
            if mode == "eva":
                left = "".join(eva[c] for c in a["word"]); right = "".join(eva[c] for c in b["word"])
                if len(ORIGINAL_GLYPHS(left)) < 2 or left[-1] not in "nlr":
                    continue
                stem, term, initial = left[:-1], left[-1], ORIGINAL_GLYPHS(right)[0]
            else:
                term = vd.terminal_class(fa["word"][-1], eva)
                if len(a["word"]) < 2 or term is None:
                    continue
                stem, initial = a["word"][:-1], b["word"][0]
            full_stem = fa["word"][:-1]
            rows.append(dict(id=f"{ln['locus']}:{i}", page=ln["page"], folio=ln["folio"], locus=ln["locus"],
                             index=i, stem=stem, terminal=term, initial=initial, kind="ordinary",
                             position=i / max(1, len(ln["words"]) - 1), paragraph_start=ln["paragraph_start"],
                             hand=ln["meta"].get("H", "?"), currier=ln["meta"].get("L", "?"),
                             section=ln["meta"].get("I", "?"), fold=ln["fold"],
                             family=g08.family("".join(eva.get(c, c) for c in full_stem)),
                             stem_key="".join(coll_table.get(c, c) for c in full_stem)))
    return rows


def run_crossed(rows, group_key, groups, glyph_fn):
    f.eva_glyphs = glyph_fn
    out = []
    try:
        for fold in range(5):
            for gf in range(5):
                train = [r for r in rows if r["fold"] != fold and groups[r[group_key]] != gf]
                test = [r for r in rows if r["fold"] == fold and groups[r[group_key]] == gf]
                if not test:
                    continue
                assert not {r[group_key] for r in train} & {r[group_key] for r in test}
                base, full = f.Model(train), f.Model(train, context=True)
                out.extend(f.score(test, base.predict(test), full.predict(test), group_key, fold))
    finally:
        f.eva_glyphs = ORIGINAL_GLYPHS
    return out


def summarize(pred, cluster):
    s = {k: v for k, v in f.summary(pred).items() if k != "gain_by_fold"} if pred else {"n": 0}
    if pred:
        s[f"gain_ci_{cluster}"] = f.cluster_ci(pred, "loss0", "loss1", cluster)
    return s


def coupling(arms, eva, mapping):
    coll_table = mapping["collapse_table"]
    families = f.assign_folds(r["family"] for r in coupling_rows(arms["full"], eva, coll_table, "units"))
    stems = f.assign_folds(r["stem_key"] for r in coupling_rows(arms["full"], eva, coll_table, "units"))
    designs = {"family_x_folio_08": ("family", families), "stem_x_folio_06": ("stem_key", stems)}
    preds = {}
    result = {"designs": {}}
    for arm, lines in list(arms.items()) + [("v101_eva", arms["full"])]:
        mode = "eva" if arm == "v101_eva" else "units"
        rows = coupling_rows(lines, eva, coll_table, mode)
        for key, groups in designs.values():
            # Bridge-arm keys absent from the unit arms (e.g. empty v101 stems) get their own folds.
            missing = {r[key] for r in rows} - set(groups)
            groups.update(f.assign_folds(missing) if missing else {})
        glyph_fn = ORIGINAL_GLYPHS if mode == "eva" else list
        for dname, (key, groups) in designs.items():
            pred = run_crossed(rows, key, groups, glyph_fn)
            preds[(arm, dname)] = pred
            cl = "family" if key == "family" else "stem_key"
            result["designs"].setdefault(dname, {})[arm] = {
                "all": summarize(pred, cl),
                **{c: summarize([r for r in pred if r["currier"] == c], cl) for c in ("A", "B")}}
            print(arm, dname, "B gain", result["designs"][dname][arm]["B"].get("gain_bits"), flush=True)
    # Replication (COLLAPSED) and paired variant contrasts.
    for dname, (key, _) in designs.items():
        d = result["designs"][dname]
        cB = d["collapsed"]["B"]
        cis = [cB.get("gain_ci_folio"), cB.get(f"gain_ci_{'family' if key == 'family' else 'stem_key'}")]
        if cB["gain_bits"] > 0 and all(ci and ci[0] > 0 for ci in cis):
            rep = "replicates on a third transcription"
        elif cB["gain_bits"] > 0:
            rep = "direction only"
        else:
            rep = "does not replicate"
        d["replication_rule_collapsed_B"] = rep
        by = {arm: {r["id"]: r for r in preds[(arm, dname)]} for arm in arms}
        paired = {}
        for subset in ("all", "A", "B"):
            ids = [i for i, r in by["full"].items() if subset == "all" or r["currier"] == subset]
            folio = [by["full"][i]["folio"] for i in ids]
            gain = {arm: np.array([by[arm][i]["loss0"] - by[arm][i]["loss1"] for i in ids]) for arm in arms}
            base = {arm: np.array([by[arm][i]["loss0"] for i in ids]) for arm in arms}
            shams = [a for a in arms if a.startswith("sham")]
            sham_gain = np.mean([gain[a] for a in shams], axis=0)
            sham_base = np.mean([base[a] for a in shams], axis=0)
            dc = boot_mean_ci(gain["full"] - gain["collapsed"], folio)
            ds = boot_mean_ci(gain["full"] - sham_gain, folio)
            paired[subset] = {
                "gain_full_minus_collapsed": dc, "gain_full_minus_sham": ds,
                "gain_full_minus_each_sham": {a: boot_mean_ci(gain["full"] - gain[a], folio)["mean"] for a in shams},
                "verdict": verdict(dc, ds),
                "base_loss_collapsed_minus_full": boot_mean_ci(base["collapsed"] - base["full"], folio),
                "base_loss_sham_minus_full": boot_mean_ci(sham_base - base["full"], folio)}
        d["paired"] = paired
    return result


# ---------------------------------------------------------------------------
# B3. Hidden boundaries (boundary.py procedure, 3-way terminal class target)
# ---------------------------------------------------------------------------

def token_lines(lines):
    """boundary.py tokenisation: uncertainty marks are stripped, empty tokens dropped."""
    out = []
    for ln in lines:
        toks = [re.sub(r"[*?]", "", w["word"]) for w in ln["words"]]
        toks = [t for t in toks if t]
        if toks:
            out.append(toks)
    return out


def hidden_boundary(tokens, term_of, first_of, units, min_n=3):
    stem_c = defaultdict(Counter); stem_next = defaultdict(Counter)
    for ts in tokens:
        for a, b in zip(ts, ts[1:]):
            t = term_of(a)
            if len(a) < 2 or t is None:
                continue
            stem = a[:-1]
            stem_c[stem][t] += 1; stem_next[(stem, first_of(b))][t] += 1
    freq = Counter(t for ts in tokens for t in ts)
    cands = []
    for joined, jf in freq.items():
        if jf > 2:
            continue
        gs = list(joined) if units else ORIGINAL_GLYPHS(joined)
        if len(gs) < 6:
            continue
        best = None
        for i in range(2, len(gs) - 2 + 1):
            left, right = "".join(gs[:i]), "".join(gs[i:])
            if freq[left] < 5 or freq[right] < 5 or len(left) < 2:
                continue
            t = term_of(left)
            if t is None:
                continue
            score = freq[left] * freq[right]
            if best is None or score > best[0]:
                best = (score, left, right, t)
        if best:
            cands.append(best)
    maj = lambda c: max("nlr", key=lambda x: c.get(x, 0))
    recs = []
    for _, left, right, t in cands:
        sc = stem_c.get(left[:-1]); ec = stem_next.get((left[:-1], first_of(right)))
        sp = maj(sc) if sc and sum(sc.values()) >= min_n else None
        ep = maj(ec) if ec and sum(ec.values()) >= min_n else None
        recs.append(dict(left=left, right=right, terminal=t, stem_pred=sp, exact_pred=ep))
    both = [r for r in recs if r["stem_pred"] and r["exact_pred"]]
    ex = np.array([r["exact_pred"] == r["terminal"] for r in both], int)
    st = np.array([r["stem_pred"] == r["terminal"] for r in both], int)
    b, c = int(((ex == 1) & (st == 0)).sum()), int(((ex == 0) & (st == 1)).sum())
    rng = np.random.default_rng(SEED)
    diffs = ex - st
    boots = [diffs[rng.integers(len(diffs), size=len(diffs))].mean() for _ in range(2000)] if len(diffs) else [np.nan]
    stem_ev = [r for r in recs if r["stem_pred"]]; ex_ev = [r for r in recs if r["exact_pred"]]
    return {"candidates": len(recs),
            "stem_only": {"n": len(stem_ev), "accuracy": float(np.mean([r["stem_pred"] == r["terminal"] for r in stem_ev])) if stem_ev else None},
            "stem_initial": {"n": len(ex_ev), "accuracy": float(np.mean([r["exact_pred"] == r["terminal"] for r in ex_ev])) if ex_ev else None},
            "both": {"n": len(both), "stem_initial_acc": float(ex.mean()) if len(both) else None,
                     "stem_only_acc": float(st.mean()) if len(both) else None,
                     "gain": float(diffs.mean()) if len(both) else None,
                     "gain_ci": [float(x) for x in np.quantile(boots, [0.025, 0.975])],
                     "mcnemar_b_c": [b, c],
                     "mcnemar_p": float(binomtest(b, b + c, 0.5).pvalue) if b + c else None}}


def boundary(arms, eva):
    out = {}
    for arm, lines in arms.items():
        term = lambda w: vd.terminal_class(w[-1], eva) if w else None
        out[arm] = hidden_boundary(token_lines(lines), term, lambda w: w[0], units=True)
        print("boundary", arm, out[arm]["both"], flush=True)
    # Bridge: EVA transliteration with the original glyph units and n/l/r as letters.
    toks = [["".join(eva.get(c, c) for c in t) for t in ts] for ts in token_lines(arms["full"])]
    out["v101_eva"] = hidden_boundary(toks, lambda w: w[-1] if w and w[-1] in "nlr" else None,
                                      lambda w: ORIGINAL_GLYPHS(w)[0], units=False)
    b = out["collapsed"]["both"]
    out["replication_rule_collapsed"] = ("replicates" if b["gain"] and b["gain"] > 0 and b["mcnemar_p"] is not None
                                         and b["mcnemar_p"] < 0.05 else "does not replicate")
    out["zl3b_reference"] = {"both_n": 624, "stem_initial_acc": 0.708, "stem_only_acc": 0.639,
                             "source": "boundary.py docstring; reproduced in REVIEW_2026-09-24.md"}
    out["note"] = "Arm comparison is descriptive: candidate sets differ between arms (protocol B3)."
    return out


# ---------------------------------------------------------------------------
# B2. §19 classifier
# ---------------------------------------------------------------------------

def equivalence(arms, eva, mapping):
    m13 = load_module("eq13", "13_equivalence_classes.py")
    eq = m13.eq
    naibbe, labels, _ = m13.naibbe_labelled()
    pairs = naibbe.pairs(); X, names = naibbe.feature_matrix(pairs)
    y = np.array([labels[i] == labels[j] for i, j in pairs], dtype=int)
    Xp = eq.select(X, names, eq.PRIMARY_GROUPS)
    models = {k: eq.make_model(k).fit(Xp, y) for k in ("logistic", "boosting")}

    def probs(corpus):
        pr = corpus.pairs(); Xa, na = corpus.feature_matrix(pr); Xa = eq.select(Xa, na, eq.PRIMARY_GROUPS)
        return pr, {k: m.predict_proba(Xa)[:, 1] for k, m in models.items()}

    zl = eq.Corpus("voynich_zl", m13.ivtff_lines(ROOT / "data/ZL3b-n.txt"))
    zl_pairs, zl_p = probs(zl)
    orig_glyphs, orig_terms = eq.eva_glyphs, eq.TERMINALS
    eq.eva_glyphs = list
    eq.TERMINALS = {c for c, img in eva.items() if img and img[-1] in "nlrm"}
    res = {"terminal_symbols": sorted(eq.TERMINALS)}
    corpora, P = {}, {}
    try:
        for arm in ("full", "collapsed"):
            lines = [[w["word"] if w["clean"] else None for w in ln["words"]] for ln in arms[arm]]
            corpora[arm] = eq.Corpus(f"v101_{arm}", lines)
            corpora[arm + "_shuffled"] = eq.Corpus(f"v101_{arm}_shuffled", m13.shuffled_lines(lines))
        for key, corpus in corpora.items():
            P[key] = probs(corpus)
            res[key] = {k: eq.high_probability_summary(corpus, p, P[key][0]) for k, p in P[key][1].items()}
            print("equivalence", key, {k: v["rate_p_ge_0.5"] for k, v in res[key].items()}, flush=True)
    finally:
        eq.eva_glyphs, eq.TERMINALS = orig_glyphs, orig_terms
    app = json.loads((ROOT / "results/equivalence_2026-09-25/application.json").read_text())
    res["reference_rates_p_ge_0.5"] = {k: {m: app[k][m]["rate_p_ge_0.5"] for m in ("logistic", "boosting")}
                                       for k in ("voynich_zl", "voynich_it", "control_assembly",
                                                 "control_copy_edit", "control_voynich_shuffled")}
    # Rule on COLLAPSED: rate exceeds both message-free controls and its own shuffle, and stable vs ZL.
    rule = {}
    for k in models:
        rate = res["collapsed"][k]["rate_p_ge_0.5"]
        ctrl = [res["reference_rates_p_ge_0.5"]["control_assembly"][k], res["reference_rates_p_ge_0.5"]["control_copy_edit"][k],
                res["collapsed_shuffled"][k]["rate_p_ge_0.5"]]
        rule[k] = {"rate": rate, "exceeds_all_controls": bool(rate > max(ctrl)), "max_control": max(ctrl)}
    # Stability vs ZL on EVA-transliterated type pairs.
    C = corpora["collapsed"]
    tr = lambda w: "".join(eva.get(c, c) for c in w)
    stab = {}
    for k in models:
        dz = {(zl.types[i], zl.types[j]): p for (i, j), p in zip(zl_pairs, zl_p[k])}
        dc = {}
        for (i, j), p in zip(P["collapsed"][0], P["collapsed"][1][k]):
            a, b = sorted((tr(C.types[i]), tr(C.types[j])))
            dc[(a, b)] = p
        dz = {tuple(sorted(key)): v for key, v in dz.items()}
        common = sorted(set(dz) & set(dc))
        top = lambda d: {x for x, _ in sorted(((x, d[x]) for x in common), key=lambda t: -t[1])[:100]}
        stab[k] = {"common_pairs": len(common),
                   "spearman": float(spearmanr([dz[x] for x in common], [dc[x] for x in common])[0]) if len(common) > 2 else None,
                   "top100_overlap": len(top(dz) & top(dc))}
        rule[k]["stable_vs_zl"] = stab[k]
    res["interpretation_rule_collapsed"] = rule
    # Variant-only vs one-substitution pairs in FULL.
    F = corpora["full"]; table = mapping["collapse_table"]
    col = lambda w: "".join(table.get(c, c) for c in w)
    vo, os_ = defaultdict(list), defaultdict(list)
    for n, (i, j) in enumerate(P["full"][0]):
        a, b = F.types[i], F.types[j]
        if len(a) != len(b):
            continue
        if col(a) == col(b):
            vo[len(a)].append(n)
        else:
            diff = [(x, z) for x, z in zip(a, b) if x != z]
            if len(diff) == 1 and eva.get(diff[0][0]) != eva.get(diff[0][1]):
                os_[len(a)].append(n)
    lengths = sorted(vo)
    var = {}
    for k in models:
        p = P["full"][1][k]
        pv = np.array([p[n] for L in lengths for n in vo[L]])
        po = np.array([p[n] for L in lengths for n in os_[L]])
        var[k] = {"variant_only_pairs": len(pv), "one_substitution_pairs": len(po),
                  "mean_p_variant_only": float(pv.mean()) if len(pv) else None,
                  "mean_p_one_substitution": float(po.mean()) if len(po) else None,
                  "rate_p_ge_0.5_variant_only": float((pv >= 0.5).mean()) if len(pv) else None,
                  "rate_p_ge_0.5_one_substitution": float((po >= 0.5).mean()) if len(po) else None,
                  "mannwhitney_greater_p": float(mannwhitneyu(pv, po, alternative="greater").pvalue) if len(pv) and len(po) else None,
                  "examples": sorted(((F.types[P["full"][0][n][0]], F.types[P["full"][0][n][1]], round(float(p[n]), 3))
                                      for L in lengths for n in vo[L]), key=lambda t: -t[2])[:25]}
    res["variant_only_pairs_full"] = var
    res["note"] = "All of B2 is descriptive (protocol): §19 failed its Voynich gates in EQUIVALENCE_FINDINGS."
    return res


# ---------------------------------------------------------------------------

FULL_LINES: list = []


def main():
    global FULL_LINES
    todo = sys.argv[1:] or ["coupling", "boundary", "equivalence"]
    lines, mapping = vd.load_corpus()
    FULL_LINES = lines
    eva = vd.eva_of(mapping)
    arms = vd.arms(lines, mapping)
    manifest = {"script": "code/21_v101_ports.py", "protocol": "V101_PROTOCOL.md", "seed": SEED,
                "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [ROOT / "V101_PROTOCOL.md", Path(__file__).resolve(), OUT / "mapping.json",
                                     ROOT / "data/mechanisms/voyn_101.txt", ROOT / "code/v101_data.py"]}}
    if "coupling" in todo:
        r = coupling(arms, eva, mapping)
        (OUT / "port_coupling.json").write_text(json.dumps({"manifest": manifest, **r}, indent=1))
    if "boundary" in todo:
        r = boundary(arms, eva)
        (OUT / "port_hidden_boundary.json").write_text(json.dumps({"manifest": manifest, **r}, indent=1))
    if "equivalence" in todo:
        r = equivalence(arms, eva, mapping)
        (OUT / "port_equivalence.json").write_text(json.dumps({"manifest": manifest, **r}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
