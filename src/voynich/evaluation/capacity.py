"""Information-capacity screen: can a cipher family possibly decode Voynich into the target language?

Run this before spending search budget on a family (see AGENTS.md).

The bound
---------
Suppose a decoder maps each cipher unit C_i to one plaintext symbol
P_i = f(C_i, S_i), keeping the number of symbols (and the spaces), where S_i is
a state that the decoder knows from layout (for example an alternating line
table). Then any window of n plaintext symbols is a function of the matching n
cipher units and their states, so

    H(P_1..P_n) <= H(C_1..C_n) + H(S_1..S_n).

This holds for every key of the family. One-to-one substitution,
"capacity two" homophone merging, and line- or page-alternating tables are all
of this length-preserving kind. If real plaintext needs more bits per window
than the ciphertext has, plus the state bits, no key of the family can produce
text with plaintext-like statistics, and no search budget will change that.

For families where several cipher units become one plaintext symbol (verbose
coding, glyph groups, word codes), the same comparison gives the least
expansion that could close the gap: the smallest cipher window k whose block
entropy reaches that of an m-symbol plaintext window.

Estimation
----------
Block entropies are plug-in estimates on equal-sized contiguous blocks, so the
cipher and plaintext estimates carry comparable finite-sample bias. Each text
is cut into several blocks, and a comparison uses the cipher's *highest* block
estimate against the plaintext's *lowest*, which is conservative towards
calling a family feasible. Plug-in entropy is biased downward as n grows, so
keep n small (<= 4) relative to the block size. The bound concerns the
population; the estimates are finite-sample, and the verdict is labelled as
estimated, not as an exact structural exclusion.
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


def block_entropy(units, n):
    """Plug-in entropy, in bits, of overlapping n-unit windows."""
    counts = Counter(tuple(units[i:i + n]) for i in range(len(units) - n + 1))
    total = sum(counts.values())
    return -sum(c / total * math.log2(c / total) for c in counts.values())


def blocks(units, size=BLOCK):
    return [units[i:i + size] for i in range(0, len(units) - size + 1, size)]


def entropy_profile(units, max_order=MAX_ORDER, size=BLOCK):
    """Per order n: min, max and mean block entropy over contiguous blocks of `size` units."""
    bs = blocks(units, size)
    if not bs:
        raise ValueError(f"need at least {size} units, got {len(units)}")
    prof = {}
    for n in range(1, max_order + 1):
        vals = [block_entropy(b, n) for b in bs]
        prof[n] = {"min": min(vals), "max": max(vals), "mean": sum(vals) / len(vals)}
    return {"blocks": len(bs), "block_size": size, "orders": prof}


def length_preserving_check(cipher_profile, plain_profile, state_bits=0.0):
    """Necessary condition for a length-preserving decoder, per window size n.

    gap_n = min over plaintext blocks of H_n(plain) - (max over cipher blocks of H_n(cipher) + state_bits).
    A positive gap means no key of the family can reach plaintext-like n-gram diversity.
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
STATE_BITS = {"single table": 0.0, "two tables, line/page alternation": 1.0}


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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--output", type=Path, help="write the full screen as JSON")
    args = ap.parse_args(argv)
    res = screen()
    print(f"Block entropies (bits), {res['block_size']}-unit blocks; cipher max vs plaintext min per order n.")
    for c, by_p in res["length_preserving"].items():
        for p, by_state in by_p.items():
            for state, chk in by_state.items():
                gaps = " ".join(f"n={n}:{r['gap_bits']:+.2f}" for n, r in chk["by_order"].items())
                verdict = "feasible" if chk["feasible"] else "EXCLUDED"
                print(f"{c:13s} -> {p:21s} {state:34s} gap {gaps}  {verdict}")
    for c, by_p in res["required_expansion"].items():
        for p, by_m in by_p.items():
            ratios = ", ".join(f"m={m}: {r['units_per_symbol']:.2f}" if r["units_per_symbol"] else f"m={m}: >{r['m']}"
                               for m, r in by_m.items())
            print(f"{c:13s} -> {p:21s} cipher units per plaintext symbol needed (rough): {ratios}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
