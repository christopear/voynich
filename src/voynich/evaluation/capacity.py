"""Reference-profile priority screen, not a universal cipher-family exclusion.

For a fixed deterministic decoder P=f(C,S), H(P|S)<=H(C|S).
Consequently H(P)<=H(C)+I(P;S). If plaintext windows are independent
of state, H(P)<=H(C), whether state is visible layout or hidden random choice.
Layout being observable does NOT establish that independence. Paragraph,
word-length and topic conventions can violate it. Without independence the
screen needs a justified plaintext-state information allowance, not log2 of
the number of tables. Full context-dependent decoding is outside this model.

Reference profiles, plug-in entropy, and Miller–Madow corrections are empirical
sensitivity checks. Neither supplies a universal lower bound for a language.
Expansion ratios from overlapping windows are heuristic, not parsing bounds.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from voynich.paths import ROOT

SPACE = " "
BLOCK = 20000
MAX_ORDER = 4


def stream(words, segment=list):
    """Units of a word sequence with a space unit between words (spaces are kept by the decoder)."""
    out = []
    for w in words:
        if out:
            out.append(SPACE)
        out.extend(segment(w))
    return out


def block_entropy(units, n, correction="plugin"):
    """Plug-in entropy, in bits, of overlapping n-unit windows."""
    if n < 1 or len(units) < n or correction not in {"plugin", "miller-madow"}:
        raise ValueError("invalid window or estimator")
    counts = Counter(tuple(units[i:i + n]) for i in range(len(units) - n + 1))
    total = sum(counts.values())
    value = -sum(c / total * math.log2(c / total) for c in counts.values())
    return value + ((len(counts)-1)/(2*total*math.log(2)) if correction == "miller-madow" else 0)


def blocks(units, size=BLOCK):
    return [units[i:i + size] for i in range(0, len(units) - size + 1, size)]


def entropy_profile(units, max_order=MAX_ORDER, size=BLOCK, correction="plugin"):
    """Per order n: min, max and mean block entropy over contiguous blocks of `size` units."""
    bs = blocks(units, size)
    if not bs:
        raise ValueError(f"need at least {size} units, got {len(units)}")
    prof = {}
    for n in range(1, max_order + 1):
        vals = [block_entropy(b, n, correction) for b in bs]
        prof[n] = {"min": min(vals), "max": max(vals), "mean": sum(vals) / len(vals)}
    return {"blocks": len(bs), "block_size": size, "orders": prof}


def length_preserving_check(cipher_profile, plain_profile, state_bits=0.0):
    """Necessary condition for a length-preserving decoder, per window size n.

    gap_n = min over plaintext blocks of H_n(plain) - (max over cipher blocks of H_n(cipher) + state_bits).
    Positive means disfavoured relative to these estimated reference profiles.
    state_bits is an assumed I(P;S) allowance, NOT log2(number of tables).
    """
    rows = {}
    for n, p in plain_profile["orders"].items():
        c = cipher_profile["orders"][n]
        gap = p["min"] - (c["max"] + state_bits)
        rows[n] = {"plain_min": p["min"], "cipher_max": c["max"], "state_bits": state_bits,
                   "gap_bits": gap, "feasible": gap <= 0}
    return {"by_order": rows, "feasible": all(r["feasible"] for r in rows.values())}


def required_expansion(cipher_units, plain_units, m=2, max_k=8, size=BLOCK):
    """Smallest cipher window k with H_k(cipher) >= H_m(plain), as k/m cipher units per plaintext symbol.

    Rough guide only: plug-in H_k is biased downward for large k, which overstates k.
    """
    target = min(block_entropy(b, m) for b in blocks(plain_units, size))
    cbs = blocks(cipher_units, size)
    for k in range(1, max_k + 1):
        if max(block_entropy(b, k) for b in cbs) >= target:
            return {"m": m, "k": k, "units_per_symbol": k / m, "target_bits": target}
    return {"m": m, "k": None, "units_per_symbol": None, "target_bits": target, "note": f"not reached by k={max_k}"}


# ---------------------------------------------------------------------------
# Default screen: Currier B against the project's Latin, Italian and German texts
# ---------------------------------------------------------------------------

REFERENCES = {
    "latin_celsus_medical": ("data/laboratory_sources/celsus_medical.txt", "latin"),
    "latin_pliny_medical": ("data/laboratory_sources/pliny_medical.txt", "latin"),
    "latin_alfonsi": ("data/latin_alfonsi.txt", "latin"),
    "italian_dante": ("data/italian_dante.txt", "italian"),
    "german_mhg": ("data/mhg_fh.txt", "german"),
}
STATE_BITS = {"fixed table": 0.0, "changing state; plaintext independent of state": 0.0}


def voynich_units(currier="B"):
    """Currier B clean paragraph words of ZL3b as raw EVA characters and as compound glyphs."""
    from voynich.experiments import e06_boundary_frontier as frontier
    from voynich.voynich_core import eva_glyphs
    lines = [ln for ln in frontier.load_lines(ROOT / "data/ZL3b-n.txt") if ln["meta"].get("L") == currier]
    words = [w["word"] for ln in lines for w in ln["words"] if w["clean"]]
    return {"raw EVA": stream(words), "compound EVA": stream(words, eva_glyphs)}


def reference_units(path):
    from voynich.decipher_search.core import normalize
    return stream(normalize((ROOT / path).read_text(encoding="utf-8", errors="replace")).split())


def screen(max_order=MAX_ORDER, size=BLOCK):
    ciphers = voynich_units()
    plains = {name: reference_units(path) for name, (path, _) in REFERENCES.items()}
    cprof = {k: entropy_profile(v, max_order, size) for k, v in ciphers.items()}
    pprof = {k: entropy_profile(v, max_order, size) for k, v in plains.items() if len(v) >= size}
    checks = {c: {p: {state: length_preserving_check(cprof[c], pprof[p], bits) for state, bits in STATE_BITS.items()}
                  for p in pprof} for c in cprof}
    expansion = {c: {p: {m: required_expansion(ciphers[c], plains[p], m, max_k=10, size=size) for m in (2, 3, 4)}
                     for p in pprof} for c in cprof}
    return {"block_size": size, "max_order": max_order, "cipher_profiles": cprof, "plain_profiles": pprof,
            "length_preserving": checks, "required_expansion": expansion,
            "skipped_references": sorted(set(plains) - set(pprof))}


def sensitivity_screen():
    ciphers = voynich_units()
    plains = {name: reference_units(path) for name, (path, _) in REFERENCES.items()}
    rows = []
    for size in (5000, 20000, 40000, 80000):
        for estimator in ("plugin", "miller-madow"):
            pp = {p: entropy_profile(u, size=size, correction=estimator)
                  for p, u in plains.items() if len(u) >= size}
            for cipher, units in ciphers.items():
                cp = entropy_profile(units, size=size, correction=estimator)
                for name, prof in pp.items():
                    check = length_preserving_check(cp, prof)
                    for n, v in check["by_order"].items():
                        means = [p["orders"][n]["mean"] for p in pp.values()]
                        spread = max(means)-min(means)
                        rows.append(dict(cipher=cipher, reference=name, size=size,
                            estimator=estimator, order=n, cipher_blocks=cp["blocks"],
                            reference_blocks=prof["blocks"], **v,
                            reference_mean_range_bits=spread,
                            gap_over_reference_range=v["gap_bits"]/spread if spread else None))
    return {"schema":2, "rows":rows,
        "state_assumption":"Fixed table, or plaintext-window independence from the full state window.",
        "interpretation":"Priority screen relative to references; no calibrated rejection or universal language bound.",
        "bias_limit":"Miller–Madow is a sensitivity estimator, especially limited for sparse overlapping windows.",
        "reference_spread_limit":"Range of available reference means at each block size; panels change when short sources drop out.",
        "expansion_status":"Overlapping-window heuristic only; variable parsing needs an explicit model."}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--output", type=Path, help="write the full screen as JSON")
    ap.add_argument("--sensitivity", action="store_true", help="estimator and block-size robustness checks")
    args = ap.parse_args(argv)
    res = sensitivity_screen() if args.sensitivity else screen()
    if args.sensitivity:
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x") as f:
                json.dump(res, f, indent=1)
        else:
            print(json.dumps(res, indent=1))
        return
    print(f"Block entropies (bits), {res['block_size']}-unit blocks; cipher max vs plaintext min per order n.")
    for c, by_p in res["length_preserving"].items():
        for p, by_state in by_p.items():
            for state, chk in by_state.items():
                gaps = " ".join(f"n={n}:{r['gap_bits']:+.2f}" for n, r in chk["by_order"].items())
                verdict = "not screened out" if chk["feasible"] else "REFERENCE-PROFILE GAP"
                print(f"{c:13s} -> {p:21s} {state:34s} gap {gaps}  {verdict}")
    for c, by_p in res["required_expansion"].items():
        for p, by_m in by_p.items():
            ratios = ", ".join(f"m={m}: {r['units_per_symbol']:.2f}" if r["units_per_symbol"] else f"m={m}: >{r['m']}"
                               for m, r in by_m.items())
            print(f"{c:13s} -> {p:21s} cipher units per plaintext symbol needed (rough): {ratios}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x") as f:
            json.dump(res, f, indent=1, default=str)


if __name__ == "__main__":
    main()
