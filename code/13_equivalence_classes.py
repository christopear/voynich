"""Latent equivalence-class recovery calibrated on Naibbe (CONTINUATION §19).

Specification: EQUIVALENCE_PROTOCOL.md. Findings: EQUIVALENCE_FINDINGS_2026-09-25.md.

Run: OPENBLAS_NUM_THREADS=1 uv run --locked python code/13_equivalence_classes.py
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import platform
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import sklearn
from scipy.stats import spearmanr

import equivalence as eq
import mechanism_models as mm

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "results" / "equivalence_2026-09-25"
_spec = importlib.util.spec_from_file_location("frontier", Path(__file__).with_name("06_boundary_frontier.py"))
frontier = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(frontier)


# ---------------------------------------------------------------------------
# Corpus loading
# ---------------------------------------------------------------------------

def text_lines(path: Path) -> list[list[str | None]]:
    return [[None if w == "?" else w for w in ln.split()] for ln in path.read_text(encoding="utf-8").splitlines() if ln.split()]


def ivtff_lines(path: Path) -> list[list[str | None]]:
    return [[w["word"] if w["clean"] else None for w in ln["words"]] for ln in frontier.load_lines(path)]


def naibbe_labelled():
    lines = text_lines(DATA / "naibbe_cipher_pre.txt")
    cipher = (DATA / "naibbe_cipher_pre.txt").read_text().split()
    plain = (DATA / "naibbe_plain_units.txt").read_text().split()
    assert len(cipher) == len(plain)
    lab = defaultdict(Counter)
    for c, p in zip(cipher, plain):
        lab[c][p] += 1
    corpus = eq.Corpus("naibbe", lines)
    labels = [lab[w].most_common(1)[0][0] for w in corpus.types]
    purity = min(lab[w].most_common(1)[0][1] / corpus.freq[w] for w in corpus.types)
    return corpus, labels, purity


def encoded_corpus(name: str, text_file: str, n_tokens: int | None, line_lengths: list[int]):
    """Invertible Naibbe-table encoding with exact labels from decoding."""
    encoder = mm.Encoder(DATA / "mechanisms" / "naibbe_tables.csv")
    plain = mm.clean_plain((DATA / text_file).read_text())
    config = dict(mechanism="encoding", level=1, coupling=0)
    if n_tokens is None:
        # One pass without wrapping: shrink until the generator does not wrap.
        n_tokens = int(len(plain) / 1.6)
        while True:
            words, audit = mm.generate(None, encoder, plain, n_tokens, config, eq.SEED)
            if audit["source_wraps"] == 0:
                break
            n_tokens -= 500
    else:
        words, audit = mm.generate(None, encoder, plain, n_tokens, config, eq.SEED)
    lines, k, it = [], 0, iter(words)
    while True:
        chunk = [w for _, w in zip(range(line_lengths[k % len(line_lengths)]), it)]
        if not chunk:
            break
        lines.append(chunk); k += 1
    corpus = eq.Corpus(name, lines)
    labels = [encoder.reverse[w] for w in corpus.types]
    return corpus, labels, audit


def shuffled_lines(lines, seed=eq.SEED):
    flat = [w for ln in lines for w in ln]
    random.Random(seed).shuffle(flat)
    out, it = [], iter(flat)
    for ln in lines:
        out.append([next(it) for _ in ln])
    return out


# ---------------------------------------------------------------------------
# Naibbe calibration
# ---------------------------------------------------------------------------

def naibbe_cv(corpus, labels, X, names, pairs, y):
    out = {}
    base_col = names.index("cos_lr")
    designs = {"type_held_out": list(corpus.types), "class_held_out": labels}
    Xp = eq.select(X, names, eq.PRIMARY_GROUPS)
    for design, group in designs.items():
        d = {}
        preds = {}
        for kind in ("logistic", "boosting"):
            p, fold = eq.grouped_cv(pairs, y, Xp, group, kind)
            preds[kind] = (p, fold)
        mask = preds["logistic"][1] >= 0
        ev_pairs = [pr for pr, m in zip(pairs, mask) if m]
        d["evaluated_pairs"] = int(mask.sum())
        d["baseline_context_cosine"] = eq.metrics(y[mask], X[mask, base_col], ev_pairs)
        d["baseline_context_cosine"]["bootstrap"] = eq.type_bootstrap(y[mask], X[mask, base_col], ev_pairs)
        for kind, (p, fold) in preds.items():
            m = eq.metrics(y[mask], p[mask], ev_pairs)
            m["bootstrap"] = eq.type_bootstrap(y[mask], p[mask], ev_pairs)
            m["fold_roc_auc"] = [float(eq.roc_auc_score(y[fold == f], p[fold == f])) for f in range(5)
                                 if len(set(y[fold == f])) == 2]
            d[kind] = m
        # Position features: sensitivity only.
        p, fold = eq.grouped_cv(pairs, y, eq.select(X, names, eq.PRIMARY_GROUPS + ("position",)), group, "logistic")
        d["logistic_plus_position"] = {k: v for k, v in eq.metrics(y[mask], p[mask], ev_pairs).items()
                                       if k in ("roc_auc", "pr_auc")}
        # Ablations (logistic).
        abl = {}
        variants = {f"only_{g}": (g,) for g in eq.PRIMARY_GROUPS}
        variants.update({f"without_{g}": tuple(x for x in eq.PRIMARY_GROUPS if x != g) for g in eq.PRIMARY_GROUPS})
        for label, groups in variants.items():
            p, _ = eq.grouped_cv(pairs, y, eq.select(X, names, groups), group, "logistic")
            abl[label] = {k: v for k, v in eq.metrics(y[mask], p[mask], ev_pairs).items() if k in ("roc_auc", "pr_auc")}
        d["ablations_logistic"] = abl
        # Clustering inside each held-out fold.
        pc, _ = eq.grouped_cv(pairs, y, X[:, [base_col]], group, "logistic")
        folds = eq.assign_folds(group)
        cl = {"logistic": [], "context_cosine_logistic": []}
        for f in range(5):
            members = [t for t in range(len(corpus.types)) if folds[group[t]] == f]
            local = {t: k for k, t in enumerate(members)}
            idx = [n for n, (a, b) in enumerate(pairs) if a in local and b in local]
            lp = [(local[pairs[n][0]], local[pairs[n][1]]) for n in idx]
            truth = [labels[t] for t in members]
            for key, pp in (("logistic", preds["logistic"][0]), ("context_cosine_logistic", pc)):
                cl[key].append(eq.cluster_scores(truth, eq.cluster(len(members), lp, pp[idx])))
        d["clustering_p0.5"] = {k: {m: float(np.mean([r[m] for r in v])) for m in v[0]} for k, v in cl.items()}
        out[design] = d
    return out


def evaluate_labelled(corpus, labels, models):
    pairs = corpus.pairs(); X, names = corpus.feature_matrix(pairs)
    y = np.array([labels[i] == labels[j] for i, j in pairs], dtype=int)
    Xp = eq.select(X, names, eq.PRIMARY_GROUPS)
    res = {"types": len(corpus.types), "classes": len(set(labels)),
           "baseline_context_cosine": eq.metrics(y, X[:, names.index("cos_lr")], pairs)}
    for kind, model in models.items():
        p = model.predict_proba(Xp)[:, 1]
        res[kind] = eq.metrics(y, p, pairs)
        res[kind]["bootstrap"] = eq.type_bootstrap(y, p, pairs)
        res[kind]["clustering_p0.5"] = eq.cluster_scores(labels, eq.cluster(len(corpus.types), pairs, p))
        res[kind]["high_probability"] = eq.high_probability_summary(corpus, p, pairs)
    return res


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    naibbe, labels, purity = naibbe_labelled()
    pairs = naibbe.pairs(); X, names = naibbe.feature_matrix(pairs)
    y = np.array([labels[i] == labels[j] for i, j in pairs], dtype=int)
    cv = {"types": len(naibbe.types), "classes": len(set(labels)), "min_label_purity": purity,
          "pairs": len(pairs), "positives": int(y.sum()), **naibbe_cv(naibbe, labels, X, names, pairs, y)}
    (OUT / "naibbe_cv.json").write_text(json.dumps(cv, indent=2))
    print("naibbe cv done")

    # Freeze.
    Xp = eq.select(X, names, eq.PRIMARY_GROUPS)
    models = {k: eq.make_model(k).fit(Xp, y) for k in ("logistic", "boosting")}
    coef = dict(zip(eq.features_of(), models["logistic"][-1].coef_[0].tolist()))

    # Labelled transfer.
    lengths = [len(ln) for ln in naibbe.lines]
    transfer = {}
    for name, fname, n in (("latin_alfonsi", "latin_alfonsi.txt", len((DATA / "naibbe_cipher_pre.txt").read_text().split())),
                           ("italian_dante", "italian_dante.txt", None)):
        corpus, lab, audit = encoded_corpus(name, fname, n, lengths)
        transfer[name] = {"generation_audit": audit, **evaluate_labelled(corpus, lab, models)}
    transfer["naibbe_in_sample_reference"] = evaluate_labelled(naibbe, labels, models)
    (OUT / "transfer.json").write_text(json.dumps(transfer, indent=2, default=str))
    print("transfer done")

    # Application.
    zl_lines = ivtff_lines(DATA / "ZL3b-n.txt")
    corpora = {
        "voynich_zl": eq.Corpus("voynich_zl", zl_lines),
        "voynich_it": eq.Corpus("voynich_it", ivtff_lines(DATA / "mechanisms" / "IT2a-n.txt")),
        "control_assembly": eq.Corpus("assembly", text_lines(ROOT / "results/mechanisms_2026-09-24/representative_assembly.txt")),
        "control_copy_edit": eq.Corpus("copy", text_lines(ROOT / "results/mechanisms_2026-09-24/representative_copy.txt")),
        "control_voynich_shuffled": eq.Corpus("shuffled", shuffled_lines(zl_lines)),
        "naibbe_reference": naibbe,
    }
    app = {"interpretation_rule": "Voynich classes count as evidence only if its high-probability rate clearly "
                                  "exceeds both message-free controls and shuffled Voynich, and top pairs are "
                                  "stable across ZL and IT (EQUIVALENCE_PROTOCOL.md)."}
    probs = {}
    for key, corpus in corpora.items():
        pr = corpus.pairs(); Xa, na = corpus.feature_matrix(pr); Xa = eq.select(Xa, na, eq.PRIMARY_GROUPS)
        probs[key] = {k: m.predict_proba(Xa)[:, 1] for k, m in models.items()}
        app[key] = {k: eq.high_probability_summary(corpus, probs[key][k], pr) for k in models}
    # Transcription stability.
    stab = {}
    zl, it = corpora["voynich_zl"], corpora["voynich_it"]
    for kind in models:
        dz = {(zl.types[i], zl.types[j]): p for (i, j), p in zip(zl.pairs(), probs["voynich_zl"][kind])}
        di = {(it.types[i], it.types[j]): p for (i, j), p in zip(it.pairs(), probs["voynich_it"][kind])}
        common = sorted(set(dz) & set(di))
        top = lambda d: {k for k, _ in sorted(((k, d[k]) for k in common), key=lambda t: -t[1])[:100]}
        stab[kind] = {"common_pairs": len(common), "spearman": float(spearmanr([dz[k] for k in common], [di[k] for k in common])[0]),
                      "top100_overlap": len(top(dz) & top(di))}
    app["transcription_stability"] = stab
    # Descriptive constraint checks on ZL (primary model).
    p = probs["voynich_zl"]["logistic"]; T = zl.types
    okot = [(a, b, float(q)) for (i, j), q in zip(zl.pairs(), p) for a, b in [(T[i], T[j])]
            if {a[:2], b[:2]} == {"ok", "ot"} and a[2:] == b[2:]]
    rl = [(a, b, float(q)) for (i, j), q in zip(zl.pairs(), p) for a, b in [(T[i], T[j])]
          if a[:-1] == b[:-1] and {a[-1], b[-1]} == {"r", "l"}]
    app["constraint_checks_zl_logistic"] = {
        "all_pairs_mean_p": float(p.mean()),
        "ok_ot_same_remainder_pairs": okot, "ok_ot_mean_p": float(np.mean([q for *_, q in okot])),
        "oko_oto_family": [x for x in okot if x[0][2:3] == "o"],
        "same_stem_r_l_pairs_mean_p": float(np.mean([q for *_, q in rl])), "same_stem_r_l_n": len(rl)}
    (OUT / "application.json").write_text(json.dumps(app, indent=2))

    # Voynich candidate outputs (no semantics).
    rows = []
    for n, (i, j) in enumerate(zl.pairs()):
        rows.append({"a": T[i], "b": T[j], "freq_a": zl.freq[T[i]], "freq_b": zl.freq[T[j]],
                     "p_logistic": round(float(probs["voynich_zl"]["logistic"][n]), 4),
                     "p_boosting": round(float(probs["voynich_zl"]["boosting"][n]), 4)})
    rows.sort(key=lambda r: -r["p_logistic"])
    with (OUT / "voynich_candidate_pairs.csv").open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=rows[0]); wr.writeheader(); wr.writerows(rows[:1000])
    cl = eq.cluster(len(T), zl.pairs(), probs["voynich_zl"]["logistic"])
    groups = defaultdict(list)
    for t, c in zip(T, cl):
        groups[int(c)].append({"type": t, "freq": zl.freq[t]})
    clusters = sorted((v for v in groups.values() if len(v) > 1), key=lambda v: -sum(x["freq"] for x in v))
    (OUT / "voynich_candidate_clusters.json").write_text(json.dumps(
        {"note": "Candidate groupings from the frozen Naibbe-trained logistic model at p=0.5. "
                 "Hypotheses only; no semantic interpretation. See interpretation rule in application.json.",
         "clusters": clusters}, indent=2))

    manifest = {"script": "code/13_equivalence_classes.py", "protocol": "EQUIVALENCE_PROTOCOL.md",
                "seed": eq.SEED, "min_freq": eq.MIN_FREQ, "top_context": eq.TOP_CONTEXT,
                "primary_features": eq.features_of(), "position_features": eq.FEATURE_GROUPS["position"],
                "frozen_logistic_standardized_coefficients": coef,
                "python": platform.python_version(), "numpy": np.__version__, "sklearn": sklearn.__version__,
                "inputs_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [
                    DATA / "naibbe_cipher_pre.txt", DATA / "naibbe_plain_units.txt", DATA / "ZL3b-n.txt",
                    DATA / "mechanisms/IT2a-n.txt", DATA / "mechanisms/naibbe_tables.csv", DATA / "latin_alfonsi.txt",
                    DATA / "italian_dante.txt", ROOT / "results/mechanisms_2026-09-24/representative_assembly.txt",
                    ROOT / "results/mechanisms_2026-09-24/representative_copy.txt"]}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("done")


if __name__ == "__main__":
    main()
