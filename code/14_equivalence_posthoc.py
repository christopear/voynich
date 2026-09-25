"""Post-hoc diagnostics for the equivalence stage (explicitly NOT prospective).

Added after seeing 13_equivalence_classes.py results, to explain why the
message-free controls received many high-probability pairs and to check the
frozen model against the earlier r/l following-initial result. Writes
results/equivalence_2026-09-25/posthoc_diagnostics.json.
"""
import csv
import importlib.util
import json
from pathlib import Path

import numpy as np

import equivalence as eq

_spec = importlib.util.spec_from_file_location("m13", Path(__file__).with_name("13_equivalence_classes.py"))
m13 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(m13)
OUT = m13.OUT
# r/l families whose following-initial distributions differ (reconstruction.claim_rl_families).
SIGNIFICANT_RL_STEMS = ["a", "sho", "o", "sha", "cho", "da", "do", "oka", "lo", "cheo", "so", "sa",
                        "qoka", "ota", "qo", "qota"]


def main():
    zl = m13.ivtff_lines(m13.DATA / "ZL3b-n.txt")
    naibbe, labels, _ = m13.naibbe_labelled()
    corpora = {"naibbe": naibbe, "voynich_zl": eq.Corpus("zl", zl),
               "control_assembly": eq.Corpus("a", m13.text_lines(m13.ROOT / "results/mechanisms_2026-09-24/representative_assembly.txt")),
               "control_copy_edit": eq.Corpus("c", m13.text_lines(m13.ROOT / "results/mechanisms_2026-09-24/representative_copy.txt")),
               "control_voynich_shuffled": eq.Corpus("s", m13.shuffled_lines(zl))}
    medians = {}
    for key, c in corpora.items():
        X, names = c.feature_matrix()
        medians[key] = {f: float(np.median(X[:, names.index(f)]))
                        for f in ("cos_lr", "cos_left_nocatch", "cos_right_nocatch", "js_next_initial")}
    pairs = naibbe.pairs(); X, names = naibbe.feature_matrix(pairs)
    y = np.array([labels[i] == labels[j] for i, j in pairs], dtype=int)
    model = eq.make_model("logistic").fit(eq.select(X, names, eq.PRIMARY_GROUPS), y)
    z = corpora["voynich_zl"]; P = z.pairs(); Xz, nz = z.feature_matrix(P)
    p = model.predict_proba(eq.select(Xz, nz, eq.PRIMARY_GROUPS))[:, 1]
    prob = {frozenset((z.types[i], z.types[j])): float(q) for (i, j), q in zip(P, p)}
    rl = [{"l": s + "l", "r": s + "r", "p": prob[frozenset((s + "l", s + "r"))]}
          for s in SIGNIFICANT_RL_STEMS if frozenset((s + "l", s + "r")) in prob]
    out = {"status": "post hoc, exploratory",
           "median_pair_features": medians,
           "significant_rl_family_pairs": rl,
           "significant_rl_pairs_merged_p_ge_0.5": sum(r["p"] >= 0.5 for r in rl)}
    (OUT / "posthoc_diagnostics.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
