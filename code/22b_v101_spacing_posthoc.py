"""Post hoc (not in the protocol): where do v101 and ZL3b spaces disagree, and what gain do those observations carry?

For corpus ZV (ZL letters, v101 spaces) each ordinary space is classed by what
ZL3b has in the same aligned column: an ordinary space, an uncertain space, a
drawing gap, or no space (v101 splits a ZL token). Symmetrically for ZZ
(ZL spaces) by what v101 has. Gains come from re-running the same
deterministic 08 design as 22_v101_gain_decomposition.py.

Run: OPENBLAS_NUM_THREADS=1 uv run --locked python code/22b_v101_spacing_posthoc.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import defaultdict
import multiprocessing
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("g22", Path(__file__).with_name("22_v101_gain_decomposition.py"))
g = importlib.util.module_from_spec(spec); sys.modules["g22"] = g; spec.loader.exec_module(g)

NAME = {None: "none", ".": "ordinary", ",": "uncertain", "|": "drawing"}


def categories(pairs, eva):
    """(ZL locus, gap index) -> category of the other transcription's column, for ZV and ZZ separators."""
    out = {"ZV": {}, "ZZ": {}}
    for zl, vl in pairs:
        cols = g.align_chars(g.line_string(zl["words"], zl["gaps"]), g.line_string(vl["words"], vl["gaps"], eva))
        kz = kv = 0
        for a, b in cols:
            if b is not None and g.is_sep(b):          # a separator emitted in ZV
                out["ZV"][(zl["locus"], kv)] = NAME[a if a is None or g.is_sep(a) else None]
                kv += 1
            if a is not None and g.is_sep(a):          # a separator emitted in ZZ
                out["ZZ"][(zl["locus"], kz)] = NAME[b if b is None or g.is_sep(b) else None]
                kz += 1
    return out


def main():
    b = g.build()
    cats = categories(b["pairs"], b["eva"])
    with multiprocessing.get_context("fork").Pool(2, initializer=g.init, initargs=(b["fams"],)) as pool:
        preds = dict(pool.map(g.job, [(k, b["all_rows"][k]) for k in ("ZV", "ZZ")]))
    res = {"note": "POST HOC, descriptive; not covered by V101_FOLLOWUP_PROTOCOL.md decision rules."}
    for corpus, other in (("ZV", "ZL3b"), ("ZZ", "v101")):
        for subset in ("B", "all"):
            groups = defaultdict(list)
            for r in preds[corpus]:
                if subset == "B" and r["currier"] != "B":
                    continue
                groups[cats[corpus].get((r["locus"], r["index"]), "unmatched")].append(r)
            res[f"{corpus}_by_{other}_column_{subset}"] = {
                k: {"n": len(v), "gain_bits": float(np.mean([r["loss0"] - r["loss1"] for r in v])),
                    "gain_ci_folio": g.f.cluster_ci(v, "loss0", "loss1", "folio"),
                    "accuracy_base": float(np.mean([r["correct0"] for r in v])),
                    "accuracy_full": float(np.mean([r["correct1"] for r in v]))}
                for k, v in sorted(groups.items())}
    (g.OUT / "spacing_posthoc.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
