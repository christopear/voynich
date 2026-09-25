"""Coupling-aware equivalence test for terminal alternations.

Specification: COUPLING_TEST_PROTOCOL.md. Findings: COUPLING_TEST_FINDINGS_2026-09-25.md.

Run: OPENBLAS_NUM_THREADS=1 uv run --locked python code/16_coupling_aware_test.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import random
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon
from sklearn.metrics import roc_auc_score

import coupling_test as ct
import mechanism_models as mm
import slot_cipher as sc

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "results" / "coupling_test_2026-09-25"
_spec = importlib.util.spec_from_file_location("m13", Path(__file__).with_name("13_equivalence_classes.py"))
m13 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(m13)

CAL_SEEDS = (201, 202, 203)
MAX_PAIRS = 150
CIPHER_FINALS = set("ynlrm")
VOYNICH_FINALS = set("nlr")
SENS_FINALS = set("nlrmy")


def token_lines(laid):
    return [[w["word"] if w["clean"] else None for w in ln["words"]] for ln in laid]


def frac(xs):
    return float(np.mean(xs)) if len(xs) else None


def calibration(template, training, syllables):
    counts = Counter(syllables)
    out = {}
    for beta in (2.0, 0.0):
        rows = []
        for seed in CAL_SEEDS:
            cfg = sc.Config(10, 1.0, beta)
            book = sc.SharedCoreCodeBook(counts, training, cfg, seed)
            words = sc.encipher(syllables, book, training.edge, cfg, seed + 5000)
            occ = ct.Occurrences(token_lines(mm.apply_template(template, words)))
            pairs = ct.same_stem_pairs(occ, CIPHER_FINALS)
            kinds = {"same_unit": [p for p in pairs if book.decode[p[0]] == book.decode[p[1]]],
                     "distinct_unit": [p for p in pairs if book.decode[p[0]] != book.decode[p[1]]]}
            rng = random.Random(seed)
            for kind, ps in kinds.items():
                for a, b in rng.sample(ps, min(MAX_PAIRS, len(ps))):
                    rows.append({"seed": seed, "kind": kind, "eligible_of_kind": len(ps), **ct.score_pair(occ, a, b)})
            print("calibration beta", beta, "seed", seed, {k: len(v) for k, v in kinds.items()}, flush=True)
        same = [r for r in rows if r["kind"] == "same_unit"]; dist = [r for r in rows if r["kind"] == "distinct_unit"]
        pct = lambda rs: float(np.median([r["ref_percentile"] for r in rs if r["ref_percentile"] is not None]))
        summary = {
            "n_same": len(same), "n_distinct": len(dist),
            "same_sig_rate": frac([r["p"] < 0.05 for r in same]),
            "distinct_sig_rate": frac([r["p"] < 0.05 for r in dist]),
            "auc_excess_distinct_vs_same": float(roc_auc_score([0] * len(same) + [1] * len(dist),
                                                               [r["excess"] for r in same + dist])),
            "median_ref_percentile_same": pct(same), "median_ref_percentile_distinct": pct(dist),
            "naive_same_sig_rate": frac([r["naive"]["p"] < 0.05 for r in same]),
            "naive_distinct_sig_rate": frac([r["naive"]["p"] < 0.05 for r in dist]),
            "naive_auc_distinct_vs_same": float(roc_auc_score([0] * len(same) + [1] * len(dist),
                                                              [r["naive"]["excess"] for r in same + dist])),
            "category_counts_same": Counter(ct.category(r) for r in same),
            "category_counts_distinct": Counter(ct.category(r) for r in dist)}
        if beta == 2.0:
            summary["C1_size"] = summary["same_sig_rate"] <= 0.10
            summary["C2_power"] = summary["distinct_sig_rate"] >= 0.50 and summary["auc_excess_distinct_vs_same"] >= 0.80
            summary["C3_reference"] = summary["median_ref_percentile_same"] <= 25 and summary["median_ref_percentile_distinct"] >= 40
            summary["calibration_passed"] = summary["C1_size"] and summary["C2_power"] and summary["C3_reference"]
        out[f"beta_{beta:g}"] = {"summary": summary, "pairs": rows}
    return out


def voynich(lines, finals, **kw):
    occ = ct.Occurrences(lines)
    rows = [ct.score_pair(occ, a, b, **kw) for a, b in ct.same_stem_pairs(occ, finals)]
    for r in rows:
        r["category"] = ct.category(r)
    pcts = [r["ref_percentile"] for r in rows if r["ref_percentile"] is not None]
    agg = {"pairs": len(rows), "with_reference": len(pcts),
           "median_ref_percentile": float(np.median(pcts)) if pcts else None,
           "wilcoxon_p": float(wilcoxon(np.array(pcts) - 50).pvalue) if len(pcts) >= 5 else None,
           "category_counts": Counter(r["category"] for r in rows),
           "sig_rate": frac([r["p"] < 0.05 for r in rows]),
           "naive_sig_rate": frac([r["naive"]["p"] < 0.05 for r in rows])}
    m, p = agg["median_ref_percentile"], agg["wilcoxon_p"]
    if m is None:
        agg["interpretation"] = "no pairs"
    elif m <= 25 and p is not None and p < 0.05:
        agg["interpretation"] = "class behaves like edge-conditioned variants (compatible with homophony)"
    elif m >= 40:
        agg["interpretation"] = "context beyond boundary glyphs, like random distinct pairs (against pure edge-conditioned homophony)"
    else:
        agg["interpretation"] = "mixed / undetermined"
    return {"aggregate": agg, "pairs": rows}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    template = m13.frontier.load_lines(DATA / "ZL3b-n.txt")
    training = mm.Training(template)
    n_slots = sum(len(ln["words"]) for ln in template)
    syllables = sc.syllable_stream((DATA / "latin_alfonsi.txt").read_text(encoding="utf-8", errors="replace"))[:n_slots]

    cal = calibration(template, training, syllables)
    (OUT / "calibration.json").write_text(json.dumps(cal, indent=2, default=dict))
    passed = cal["beta_2"]["summary"]["calibration_passed"]
    print("calibration", json.dumps(cal["beta_2"]["summary"], default=dict), flush=True)

    zl = m13.ivtff_lines(DATA / "ZL3b-n.txt")
    it = m13.ivtff_lines(DATA / "mechanisms" / "IT2a-n.txt")
    res = {"calibration_passed": passed,
           "zl": voynich(zl, VOYNICH_FINALS), "it": voynich(it, VOYNICH_FINALS),
           "sensitivity_zl_finals_nlrmy": voynich(zl, SENS_FINALS)["aggregate"],
           "sensitivity_zl_two_glyph_z": voynich(zl, VOYNICH_FINALS, z_mode="two")["aggregate"],
           "sensitivity_zl_left_only": voynich(zl, VOYNICH_FINALS, sides="left")["aggregate"]}
    cz = {(r["a"], r["b"]): r["category"] for r in res["zl"]["pairs"]}
    ci = {(r["a"], r["b"]): r["category"] for r in res["it"]["pairs"]}
    shared = sorted(set(cz) & set(ci))
    res["stability"] = {"shared_pairs": len(shared), "same_category": sum(cz[k] == ci[k] for k in shared),
                        "cross_tab": Counter(f"{cz[k]}|{ci[k]}" for k in shared)}
    if not passed:
        res["note"] = "Calibration failed: Voynich results are reported but not interpreted (protocol)."
    (OUT / "voynich.json").write_text(json.dumps(res, indent=2, default=dict))
    manifest = {"script": "code/16_coupling_aware_test.py", "protocol": "COUPLING_TEST_PROTOCOL.md",
                "top_k": ct.TOP_K, "reps": ct.REPS, "seed": ct.SEED, "calibration_seeds": CAL_SEEDS,
                "max_pairs_per_kind": MAX_PAIRS, "python": platform.python_version(), "numpy": np.__version__,
                "inputs_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [
                    DATA / "ZL3b-n.txt", DATA / "mechanisms/IT2a-n.txt", DATA / "latin_alfonsi.txt"]}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({k: res[k]["aggregate"] if k in ("zl", "it") else res[k] for k in res if k != "note"},
                     indent=2, default=dict))


if __name__ == "__main__":
    main()
