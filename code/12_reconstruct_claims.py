"""Recompute handoff claims whose original experiment drivers were lost.

Writes results/reconstruction_2026-09-25/claims.json (one entry per claim with
snapshot value, reconstructed value, status and definition), a parser
sensitivity rerun using corrected alternative-reading handling, and a manifest
of input hashes. See RECONSTRUCTION_FINDINGS_2026-09-25.md.

Usage:
    uv run --locked python code/12_reconstruct_claims.py [--only NAME ...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

from voynich_core import parse_zl3b
from reconstruction import ALL_CLAIMS, PARSER_SENSITIVE, Corpora

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "results" / "reconstruction_2026-09-25"
INPUTS = ("ZL3b-n.txt", "naibbe_cipher_pre.txt", "naibbe_cipher_respaced.txt", "naibbe_plain_units.txt",
          "latin_alfonsi.txt", "italian_dante.txt", "mhg_fh.txt")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", choices=sorted(ALL_CLAIMS), help="run a subset of claims")
    ap.add_argument("--skip-parser-sensitivity", action="store_true")
    args = ap.parse_args()
    names = args.only or list(ALL_CLAIMS)
    OUT.mkdir(parents=True, exist_ok=True)

    pages, lines = parse_zl3b(DATA / "ZL3b-n.txt")
    corpora = Corpora(DATA, pages, lines)
    claims = {}
    for name in names:
        t = time.time()
        claims[name] = ALL_CLAIMS[name](corpora)
        print(f"{name:28s} {claims[name]['status']:15s} {time.time() - t:6.1f}s", file=sys.stderr)
    path = OUT / ("claims.json" if not args.only else "claims_subset.json")
    path.write_text(json.dumps(claims, indent=2, default=str))

    if not args.skip_parser_sensitivity:
        pages_f, lines_f = parse_zl3b(DATA / "ZL3b-n.txt", fix_alternatives=True)
        fixed = Corpora(DATA, pages_f, lines_f)
        sens = {"description": "Parser-dependent claims rerun with fix_alternatives=True "
                               "(first reading kept for every [a:b] alternative).",
                "tokens_original": len(corpora.full), "tokens_fixed": len(fixed.full),
                "types_original": len(corpora.freq), "types_fixed": len(fixed.freq), "claims": {}}
        for name in PARSER_SENSITIVE:
            if name in names:
                r = ALL_CLAIMS[name](fixed)
                sens["claims"][name] = {"original_parser": claims[name]["reconstructed"],
                                        "fixed_parser": r["reconstructed"]}
        (OUT / "parser_sensitivity.json").write_text(json.dumps(sens, indent=2, default=str))

    manifest = {
        "script": "code/12_reconstruct_claims.py",
        "python": platform.python_version(),
        "claims_run": names,
        "inputs_sha256": {n: hashlib.sha256((DATA / n).read_bytes()).hexdigest() for n in INPUTS},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    for name, r in claims.items():
        print(f"\n[{r['status']}] {r['claim']}\n  snapshot:      {r['snapshot']}\n  reconstructed: {r['reconstructed']}")


if __name__ == "__main__":
    main()
