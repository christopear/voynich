"""Step B of CIPHER_FAMILY_PROTOCOL.md: can surviving families' homophone groups be recovered, and what does Voynich show?

Run after 24: OPENBLAS_NUM_THREADS=1 uv run --locked python code/25_homophone_recovery.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import multiprocessing
import random
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

import cipher_families as cf
import equivalence as eq
import mechanism_models as mm

ROOT = cf.ROOT
OUT = ROOT / "results/cipher_families_2026-09-26"
HOMOPHONIC = ("F2_homophonic", "F3_nomenclator", "F5_verbose_naibbe", "F6_verbose_syllabic", "F7_verbose_nulls")
MIN_FREQ = 10
TRAIN_SEEDS, TEST_SEEDS = (1, 2), (3,)
SHUFFLE_SEED = 20260925
W = {}


def setup():
    w1, w2, train = cf.currier_b_windows()
    W.update(layout=w1 + w2, training=mm.Training(train))


def token_lines(laid):
    return [[w["word"] if w["clean"] else None for w in ln["words"]] for ln in laid]


def labelled(job):
    config, seed = job
    laid, labels = cf.simulate(config, W["layout"], seed, W["training"])
    if laid is None:
        return config, seed, None
    per_type = {}
    for w, l in zip((w["word"] for ln in laid for w in ln["words"]), labels):
        per_type.setdefault(w, Counter())[l] += 1
    return config, seed, (token_lines(laid), {w: c.most_common(1)[0][0] for w, c in per_type.items()})


def corpus_xy(lines, label_of=None):
    c = eq.Corpus("x", lines, min_freq=MIN_FREQ)
    pairs = c.pairs()
    X, names = c.feature_matrix(pairs)
    X = eq.select(X, names, eq.PRIMARY_GROUPS)
    y = None if label_of is None else np.array([label_of[c.types[i]] == label_of[c.types[j]] for i, j in pairs], int)
    return c, pairs, X, y


def precision_at(y, p, t=0.8):
    m = p >= t
    return float(y[m].mean()) if m.any() else None, int(m.sum())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    verdicts = json.loads((OUT / "step_a_verdicts.json").read_text())
    gates = json.loads((OUT / "step_a_gates.json").read_text())
    robust = verdicts["summary"]["robust_ZL"]
    surviving = [f for f in HOMOPHONIC if robust[f] == "compatible"]
    scope = set(surviving)
    for a, b in gates["confusable_pairs"]:
        if a in surviving and b in HOMOPHONIC:
            scope.add(b)
        if b in surviving and a in HOMOPHONIC:
            scope.add(a)
    apply_to_voynich = bool(surviving)
    if not surviving:
        scope = {"F5_verbose_naibbe", "F6_verbose_syllabic"}
    print("surviving", surviving, "scope", sorted(scope), flush=True)

    compat = {f: [] for f in scope}
    runs = json.loads((OUT / "step_a_runs.json").read_text())
    # Compatible configurations (either ZL window), recomputed from the saved verdict inputs.
    spec = importlib.util.spec_from_file_location("s24", Path(__file__).with_name("24_cipher_family_benchmark.py"))
    s24 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s24)
    for win in ("W1", "W2"):
        stats, fam = s24.config_stats(runs, win)
        vec = np.array([verdicts["targets"][f"ZL_{win}"][k] for k in cf.PRIMARY])
        sdv = np.array([verdicts["target_bootstrap_sd"][f"ZL_{win}"][k] for k in cf.PRIMARY])
        for key, (mu, sd) in stats.items():
            if fam[key] in scope and np.max(np.abs((vec - mu) / np.sqrt(sd ** 2 + sdv ** 2))) <= s24.Z_MAX:
                compat[fam[key]].append(key)
    configs = {cf.config_key(c): c for c in cf.configurations()}

    result = {"surviving_families": surviving, "scope": sorted(scope), "voynich_application": apply_to_voynich, "families": {}}
    voy_lines = token_lines(W["layout"])
    V = corpus_xy(voy_lines)
    flat = [w for ln in voy_lines for w in ln]
    random.Random(SHUFFLE_SEED).shuffle(flat)
    it = iter(flat)
    shuffled = [[next(it) for _ in ln] for ln in voy_lines]
    S = corpus_xy(shuffled)
    refs = {}
    for rf in ("R1_assembly", "R2_copy"):
        key = verdicts["verdicts"]["ZL_W1"][rf]["best_key"]
        laid, _ = cf.simulate(configs[key], W["layout"], 1, W["training"])
        refs[rf] = (key, corpus_xy(token_lines(laid)))

    for fam in sorted(scope):
        keys = sorted(set(compat[fam])) if len(set(compat[fam])) >= 2 else \
            sorted(k for k, c in configs.items() if c["family"] == fam)
        langs = ["latin"] if fam in ("F2_homophonic", "F3_nomenclator") else ["latin", "german"]
        keys = [k for k in keys if configs[k]["language"] in langs]
        jobs = [(configs[k], s) for k in keys for s in TRAIN_SEEDS + TEST_SEEDS]
        with multiprocessing.get_context("fork").Pool(4) as pool:
            data = pool.map(labelled, jobs)
        built = []
        for config, seed, d in data:
            if d is None:
                continue
            c, pairs, X, y = corpus_xy(*d)
            if y.sum() == 0:
                continue
            built.append(dict(key=cf.config_key(config), language=config["language"], seed=seed, X=X, y=y, types=len(c.types)))
        evals = []
        # Held-out seed: train on train seeds (all languages), test on test seeds.
        splits = [("held_out_seed", lambda b: b["seed"] in TRAIN_SEEDS, lambda b: b["seed"] in TEST_SEEDS)]
        if len(langs) == 2:
            for a, b_ in (("latin", "german"), ("german", "latin")):
                splits.append((f"held_out_language_{a}_to_{b_}", lambda b, a=a: b["language"] == a and b["seed"] in TRAIN_SEEDS,
                               lambda b, b_=b_: b["language"] == b_ and b["seed"] in TEST_SEEDS))
        models = {}
        for name, tr, te in splits:
            trn = [b for b in built if tr(b)]; tst = [b for b in built if te(b)]
            if not trn or not tst:
                continue
            model = eq.make_model("logistic").fit(np.vstack([b["X"] for b in trn]), np.concatenate([b["y"] for b in trn]))
            p = np.concatenate([model.predict_proba(b["X"])[:, 1] for b in tst]); y = np.concatenate([b["y"] for b in tst])
            prec, npos = precision_at(y, p)
            evals.append(dict(split=name, auc=float(roc_auc_score(y, p)), precision_p08=prec, pairs_p08=npos,
                              positives=int(y.sum()), pairs=len(y)))
            models[name] = model
        pooled_auc = float(np.mean([e["auc"] for e in evals])) if evals else None
        precs = [e["precision_p08"] for e in evals if e["precision_p08"] is not None]
        h1 = bool(evals) and all(e["auc"] >= 0.85 for e in evals) and bool(precs) and all(x >= 0.5 for x in precs) \
            and len(precs) == len(evals)
        famres = {"configs_used": keys, "configs_from_step_a_compatible": len(set(compat[fam])) >= 2,
                  "evaluations": evals, "H1_pass": h1}
        if apply_to_voynich and h1 and fam in surviving:
            final = eq.make_model("logistic").fit(np.vstack([b["X"] for b in built]), np.concatenate([b["y"] for b in built]))
            rate = lambda X: float((final.predict_proba(X)[:, 1] >= 0.8).mean())
            syn = [rate(b["X"]) for b in built]
            c, pairs, X, _ = V
            pv = final.predict_proba(X)[:, 1]
            vr = float((pv >= 0.8).mean())
            app = {"voynich_rate_p08": vr, "voynich_types": len(c.types),
                   "family_range_5_95": [float(np.quantile(syn, 0.05)), float(np.quantile(syn, 0.95))],
                   "shuffled_voynich_rate_p08": rate(S[2]),
                   "reference_rates_p08": {rf: {"config": k, "rate": rate(v[2])} for rf, (k, v) in refs.items()}}
            app["shows_family_signature"] = (app["family_range_5_95"][0] <= vr <= app["family_range_5_95"][1]
                                             and vr > app["shuffled_voynich_rate_p08"]
                                             and all(vr > x["rate"] for x in app["reference_rates_p08"].values()))
            order = np.argsort(-pv)[:50]
            app["top_pairs"] = [(c.types[pairs[i][0]], c.types[pairs[i][1]], round(float(pv[i]), 3)) for i in order]
            famres["voynich"] = app
        result["families"][fam] = famres
        print(fam, json.dumps({k: v for k, v in famres.items() if k != "configs_used"})[:1500], flush=True)
    (OUT / "step_b_results.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    (OUT / "step_b_manifest.json").write_text(json.dumps({
        "min_freq": MIN_FREQ, "train_seeds": TRAIN_SEEDS, "test_seeds": TEST_SEEDS,
        "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in [Path(__file__).resolve(), ROOT / "code/cipher_families.py", ROOT / "CIPHER_FAMILY_PROTOCOL.md"]}}, indent=1))


if __name__ == "__main__":
    main()
