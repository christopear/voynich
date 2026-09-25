"""§19 transfer to a non-Naibbe syllabic slot cipher, with and without edge coupling.

Specification: COUPLED_CIPHER_PROTOCOL.md. Findings: COUPLED_CIPHER_FINDINGS_2026-09-25.md.

Run: OPENBLAS_NUM_THREADS=1 uv run --locked python code/15_coupled_cipher_transfer.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import math
import platform
from collections import Counter
from pathlib import Path

import numpy as np
import sklearn

import equivalence as eq
import mechanism_models as mm
import slot_cipher as sc
from voynich_core import eva_glyphs

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "results" / "coupled_cipher_2026-09-25"
_spec = importlib.util.spec_from_file_location("m13", Path(__file__).with_name("13_equivalence_classes.py"))
m13 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(m13)

GRID = [sc.Config(h, s, b) for h in (3, 6, 10) for s in (0.0, 1.0) for b in (0.0, 1.0, 2.0, 4.0)]
CAL_SEEDS = (1, 2)
EVAL_SEEDS = (101, 102, 103)


def generate(config, seed, syllables, training, template):
    book = sc.CodeBook(set(syllables), training, config, seed)
    words = sc.encipher(syllables, book, training.edge, config, seed + 5000)
    return book, words, mm.apply_template(template, words)


def token_lines(laid):
    return [[w["word"] if w["clean"] else None for w in ln["words"]] for ln in laid]


def parisel_style(lines) -> dict:
    """Our reimplementation of Parisel's E->S% and raw boundary MI (EVA glyph units)."""
    sents = [[eva_glyphs(w) for w in ln if w] for ln in lines]
    sc_, ec = Counter(), Counter()
    for s in sents:
        for g in s:
            sc_[g[0]] += 1; ec[g[-1]] += 1
    cls = {g: "start" if sc_[g] > 2 * ec[g] else "end" if ec[g] > 2 * sc_[g] else "ambig" for g in set(sc_) | set(ec)}
    pairs = [(a[-1], b[0]) for s in sents for a, b in zip(s, s[1:])]
    es = sum(cls[a] == "end" and cls[b] == "start" for a, b in pairs) / len(pairs)
    return {"es_pct": 100 * es, "boundary_mi_raw": mm.mi(pairs), "pairs": len(pairs)}


def type_parts(book, types):
    """(unit, prefix, terminal) for each cipher type."""
    out = {}
    for u, opts in book.variants.items():
        for p, t, _ in opts:
            out[book.word(u, p, t)] = (u, p, t)
    return [out[w] for w in types]


def e3_diagnostic(corpus, parts, p, pairs, X, names):
    groups = {"terminal_only_true": [], "other_true": [], "different_unit": []}
    for n, (i, j) in enumerate(pairs):
        (ua, pa, ta), (ub, pb, tb) = parts[i], parts[j]
        key = ("terminal_only_true" if ua == ub and pa == pb else "other_true") if ua == ub else "different_unit"
        groups[key].append(n)
    out = {}
    for key, idx in groups.items():
        idx = np.array(idx)
        out[key] = {"n": int(len(idx)), "mean_p": float(p[idx].mean()),
                    "mean_js_next_initial": float(X[idx, names.index("js_next_initial")].mean()),
                    "mean_cos_right_nocatch": float(X[idx, names.index("cos_right_nocatch")].mean())}
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    template = m13.frontier.load_lines(DATA / "ZL3b-n.txt")
    training = mm.Training(template)
    target = mm.fingerprint(template)
    n_slots = sum(len(ln["words"]) for ln in template)
    syllables = sc.syllable_stream((DATA / "latin_alfonsi.txt").read_text(encoding="utf-8", errors="replace"))[:n_slots]
    assert len(syllables) == n_slots

    # Calibration.
    runs = []
    for config, seed in itertools.product(GRID, CAL_SEEDS):
        _, words, laid = generate(config, seed, syllables, training, template)
        fp = mm.fingerprint(laid)
        runs.append({**config.__dict__, "seed": seed, "distance": mm.calibration_distance(fp, target),
                     **{k: fp[k] for k in mm.CALIBRATION_SCALES}, "corpus_sha": hashlib.sha256("\n".join(words).encode()).hexdigest()})
        print("cal", config, seed, round(runs[-1]["distance"], 3), flush=True)
    scores = []
    for config in GRID:
        rs = [r for r in runs if (r["h"], r["s"], r["beta"]) == (config.h, config.s, config.beta)]
        scores.append({**config.__dict__, "mean_distance": float(np.mean([r["distance"] for r in rs])),
                       "edge_mi": [r["edge_mi"] for r in rs]})
    key = lambda r: (r["mean_distance"], r["h"], r["beta"])
    r0 = min((r for r in scores if r["beta"] == 0), key=key)
    r1 = min((r for r in scores if r["beta"] > 0), key=key)
    manipulation = all(a > b for a, b in zip(r1["edge_mi"], r0["edge_mi"]))
    selection = {"R0": r0, "R1": r1, "manipulation_check_R1_edge_mi_exceeds_R0_both_seeds": manipulation,
                 "voynich_target": {k: target[k] for k in mm.CALIBRATION_SCALES}}
    (OUT / "calibration.json").write_text(json.dumps({"target": target, "grid_scores": scores, "runs": runs}, indent=2))
    (OUT / "selection.json").write_text(json.dumps(selection, indent=2))
    regimes = {"R0": sc.Config(r0["h"], r0["s"], r0["beta"])}
    if manipulation:
        regimes["R1"] = sc.Config(r1["h"], r1["s"], r1["beta"])

    # Frozen Naibbe-trained models (deterministic refit, as in 13).
    naibbe, nlabels, _ = m13.naibbe_labelled()
    npairs = naibbe.pairs(); NX, nn = naibbe.feature_matrix(npairs)
    ny = np.array([nlabels[i] == nlabels[j] for i, j in npairs], dtype=int)
    NXp = eq.select(NX, nn, eq.PRIMARY_GROUPS)
    models = {k: eq.make_model(k).fit(NXp, ny) for k in ("logistic", "boosting")}

    transfer, realism = {}, {}
    zl_lines = token_lines(template)
    realism["voynich_zl"] = {**parisel_style(zl_lines), **{k: target[k] for k in mm.DIAGNOSTICS}}
    realism["naibbe"] = parisel_style(naibbe.lines)
    for name, config in regimes.items():
        per_seed = []
        for seed in EVAL_SEEDS:
            book, words, laid = generate(config, seed, syllables, training, template)
            lines = token_lines(laid)
            corpus = eq.Corpus(f"{name}_{seed}", lines)
            labels = [book.decode[w] for w in corpus.types]
            res = {"seed": seed, **m13.evaluate_labelled(corpus, labels, models)}
            pairs = corpus.pairs(); X, names = corpus.feature_matrix(pairs)
            p = models["logistic"].predict_proba(eq.select(X, names, eq.PRIMARY_GROUPS))[:, 1]
            res["e3"] = e3_diagnostic(corpus, type_parts(book, corpus.types), p, pairs, X, names)
            if seed == EVAL_SEEDS[0]:
                y = np.array([labels[i] == labels[j] for i, j in pairs], dtype=int)
                pcv, fold = eq.grouped_cv(pairs, y, eq.select(X, names, eq.PRIMARY_GROUPS), labels, "logistic")
                mask = fold >= 0
                res["e2_class_held_out_cv"] = {k: v for k, v in eq.metrics(
                    y[mask], pcv[mask], [pr for pr, m in zip(pairs, mask) if m]).items() if k != "reliability"}
                fp = mm.fingerprint(laid)
                realism[name] = {**parisel_style(lines), **{k: fp[k] for k in mm.DIAGNOSTICS},
                                 **{k: fp[k] for k in mm.CALIBRATION_SCALES}}
                (OUT / f"representative_{name}.txt").write_text(
                    "\n".join(" ".join(w or "?" for w in ln) for ln in lines) + "\n")
            per_seed.append(res)
            print(name, seed, round(res["logistic"]["roc_auc"], 3), flush=True)
        transfer[name] = {"config": config.__dict__, "seeds": per_seed,
                          "mean_logistic_roc_auc": float(np.mean([r["logistic"]["roc_auc"] for r in per_seed])),
                          "mean_boosting_roc_auc": float(np.mean([r["boosting"]["roc_auc"] for r in per_seed])),
                          "mean_baseline_roc_auc": float(np.mean([r["baseline_context_cosine"]["roc_auc"] for r in per_seed]))}

    # Voynich descriptive comparison for E3: same-stem r/l pairs in ZL.
    zl = eq.Corpus("zl", zl_lines); zp = zl.pairs(); ZX, zn = zl.feature_matrix(zp)
    zpv = models["logistic"].predict_proba(eq.select(ZX, zn, eq.PRIMARY_GROUPS))[:, 1]
    rl = [n for n, (i, j) in enumerate(zp) if zl.types[i][:-1] == zl.types[j][:-1]
          and {zl.types[i][-1], zl.types[j][-1]} == {"r", "l"}]
    transfer["voynich_zl_same_stem_rl"] = {"n": len(rl), "mean_p": float(zpv[rl].mean()),
                                           "mean_js_next_initial": float(ZX[rl, zn.index("js_next_initial")].mean()),
                                           "mean_cos_right_nocatch": float(ZX[rl, zn.index("cos_right_nocatch")].mean()),
                                           "all_pairs_mean_js_next_initial": float(ZX[:, zn.index("js_next_initial")].mean())}

    # Pre-set decision rules.
    decisions = {}
    if "R0" in transfer:
        a0 = transfer["R0"]["mean_logistic_roc_auc"]
        decisions["cross_family_transfer"] = "transfers" if a0 >= 0.85 else "partial" if a0 >= 0.70 else "fails"
    if "R1" in transfer:
        pairs_dir = [(s0["logistic"]["roc_auc"] - s1["logistic"]["roc_auc"],
                      s0["e3"]["terminal_only_true"]["mean_p"] - s1["e3"]["terminal_only_true"]["mean_p"])
                     for s0, s1 in zip(transfer["R0"]["seeds"], transfer["R1"]["seeds"])]
        drop = transfer["R0"]["mean_logistic_roc_auc"] - transfer["R1"]["mean_logistic_roc_auc"]
        decisions["auc_drop_R0_minus_R1"] = drop
        decisions["per_seed_auc_and_terminal_p_drops"] = pairs_dir
        decisions["coupling_blind_spot_confirmed"] = bool(drop >= 0.05 and all(d > 0 and t > 0 for d, t in pairs_dir))
        decisions["information_present_R1"] = transfer["R1"]["seeds"][0]["e2_class_held_out_cv"]["roc_auc"] >= 0.90
    transfer["decisions"] = decisions
    (OUT / "transfer.json").write_text(json.dumps(transfer, indent=2, default=str))
    (OUT / "realism.json").write_text(json.dumps(realism, indent=2))
    manifest = {"script": "code/15_coupled_cipher_transfer.py", "protocol": "COUPLED_CIPHER_PROTOCOL.md",
                "grid": [c.__dict__ for c in GRID], "calibration_seeds": CAL_SEEDS, "evaluation_seeds": EVAL_SEEDS,
                "syllable_tokens": len(syllables), "syllable_types": len(set(syllables)),
                "python": platform.python_version(), "numpy": np.__version__, "sklearn": sklearn.__version__,
                "inputs_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [
                    DATA / "ZL3b-n.txt", DATA / "latin_alfonsi.txt", DATA / "naibbe_cipher_pre.txt", DATA / "naibbe_plain_units.txt"]}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(decisions, indent=2))


if __name__ == "__main__":
    main()
