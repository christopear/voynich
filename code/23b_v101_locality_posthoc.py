"""Post hoc (not in V101_FOLLOWUP_PROTOCOL.md): where do per-row arm differences in the 08 design come from?

Splits paired per-row differences between two v101 arms into rows whose stem (or
next initial) actually differs between the arms and rows whose inputs are
identical. Differences on identical rows can only arise through the refit of
shared model coefficients (spillover), not from information in those rows.
A bijective symbol relabelling gives the numerical noise floor.

Run: OPENBLAS_NUM_THREADS=1 uv run --locked python code/23b_v101_locality_posthoc.py
"""
from __future__ import annotations

import importlib.util
import json
import multiprocessing
from pathlib import Path

import numpy as np

import v101_data as vd

spec = importlib.util.spec_from_file_location("m23", Path(__file__).with_name("23_v101_variant_followups.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

COMPARISONS = [  # (label, arm A, arm B); differences are B - A
    ("FULL_vs_COLLAPSED", ("FULL", None, 0), ("COLLAPSED", None, 0)),
    ("FULL_vs_SHAM1", ("FULL", None, 0), ("SHAM", None, 1)),
    ("FULL_vs_DROP_d", ("FULL", None, 0), ("DROP", "d", 0)),
    ("FULL_vs_DROP_r", ("FULL", None, 0), ("DROP", "r", 0)),
    ("FULL_vs_DROP_k", ("FULL", None, 0), ("DROP", "k", 0)),
    ("FULL_vs_DROP_sh", ("FULL", None, 0), ("DROP", "sh", 0)),
    ("FULL_vs_DROP_other", ("FULL", None, 0), ("DROP", "other", 0)),
    ("ADD_r_vs_ADDSHAM_r1", ("ADD", "r", 0), ("ADDSHAM", "r", 1)),
    ("FULL_vs_RELABEL_o", ("FULL", None, 0), ("RELABEL", "o", 0)),
]


def lines_for(spec_):
    kind, name, seed = spec_
    if kind == "SHAM":
        return vd.sham_lines(m.W["lines"], m.W["table"], seed)
    if kind == "RELABEL":
        return vd.represent(m.W["lines"], {name: "②"})
    return m.arm_lines(spec_)


def job(spec_):
    p21 = m.W["p21"]
    if spec_[0] == "RELABEL":
        m.W["eva"]["②"] = m.W["eva"][spec_[1]]
    rows = p21.coupling_rows(lines_for(spec_), m.W["eva"], m.W["table"], "units")
    pred = p21.run_crossed(rows, "family", m.W["families"], list)
    inputs = {r["id"]: (r["stem"], r["initial"]) for r in rows}
    return spec_, ({r["id"]: (r["loss0"], r["loss1"], r["currier"]) for r in pred}, inputs)


def main():
    specs = sorted({s for _, a, b in COMPARISONS for s in (a, b)}, key=str)
    with multiprocessing.get_context("fork").Pool(4, initializer=m.init_2a) as pool:
        res = dict(pool.map(job, specs))
    out = {"note": "POST HOC diagnostic. Positive = arm B has higher loss (worse) than arm A, in total bits."}
    for label, a, b in COMPARISONS:
        (la, ia), (lb, ib) = res[a], res[b]
        d = {}
        for what, idx in (("base", 0), ("gain", None)):
            val = {i: (lb[i][0] - la[i][0]) if idx == 0 else ((la[i][0] - la[i][1]) - (lb[i][0] - lb[i][1])) for i in la}
            stem_changed = {i for i in la if ia[i][0] != ib[i][0]}
            input_changed = {i for i in la if ia[i] != ib[i]}
            key = input_changed if what == "gain" else stem_changed
            d[what] = {"rows": len(la), "changed_rows": len(key),
                       "total_bits": float(sum(val.values())),
                       "bits_in_changed_rows": float(sum(val[i] for i in key)),
                       "bits_in_unchanged_rows": float(sum(v for i, v in val.items() if i not in key)),
                       "mean_abs_unchanged": float(np.mean([abs(v) for i, v in val.items() if i not in key]))}
        out[label] = d
        print(label, json.dumps(d), flush=True)
    (vd.ROOT / "results/v101_followup_2026-09-26/locality_posthoc.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
