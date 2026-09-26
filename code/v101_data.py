"""Shared v101 corpus for the variant test and the ports (V101_PROTOCOL.md §0).

Text lines only, with ZL3b metadata, frozen folio folds, and three word
representations: full v101, collapsed to EVA classes, and sham (variant labels
permuted within each EVA class).
"""
from __future__ import annotations

import csv
import json
import random
from collections import defaultdict

import v101

ROOT = v101.ROOT
OUT = ROOT / "results/v101_2026-09-26"
FOLD_SEED = 20260924


def load_mapping() -> dict:
    return json.loads((OUT / "mapping.json").read_text())


def eva_of(mapping: dict) -> dict[str, str]:
    return {c: s["eva"] for c, s in mapping["symbols"].items()}


def terminal_class(symbol: str, eva: dict[str, str]) -> str | None:
    """3-way EVA terminal class n/l/r of a v101 symbol, else None."""
    img = eva.get(symbol, "")
    return img[-1] if img and img[-1] in "nlr" else None


def folds_for(folios) -> dict[str, int]:
    frozen = json.loads((ROOT / "results/frontier_2026-09-24/manifest.json").read_text())["folios"]
    missing = sorted(set(folios) - set(frozen))
    random.Random(FOLD_SEED).shuffle(missing)
    out = dict(frozen)
    out.update({f: i % 5 for i, f in enumerate(missing)})
    return out


def load_corpus() -> tuple[list[dict], dict]:
    """Text lines with metadata and fold; returns (lines, mapping)."""
    mapping = load_mapping()
    lines = [ln for ln in v101.load_v101() if ln["kind"] == "text"]
    zmeta, zlines = v101.load_ivtff_all(v101.ZL_PATH)
    zby = {z["locus"]: z for z in zlines}
    aligned = {}
    with (OUT / "line_alignment.csv").open() as fh:
        for r in csv.DictReader(fh):
            aligned[r["v101_locus"]] = r["zl_locus"]
    folds = folds_for({ln["folio"] for ln in lines})
    for ln in lines:
        meta = dict(zmeta.get(ln["page"], {}))
        z = zby.get(aligned.get(ln["locus"], ""))
        if z is not None:
            meta.update(z["meta"])
        ln["meta"] = meta
        ln["fold"] = folds[ln["folio"]]
    return lines, mapping


def represent(lines: list[dict], table: dict[str, str] | None) -> list[dict]:
    """Copy of lines with every word mapped through a symbol table (None = unchanged)."""
    out = []
    for ln in lines:
        words = [dict(w, word="".join(table.get(c, c) for c in w["word"]) if table else w["word"])
                 for w in ln["words"]]
        out.append(dict(ln, words=words))
    return out


def sham_lines(lines: list[dict], collapse_table: dict[str, str], seed: int) -> list[dict]:
    """Permute v101 member symbols across all text occurrences of each EVA class."""
    members = defaultdict(set)
    for c, canon in collapse_table.items():
        members[canon].add(c)
    multi = {canon for canon, m in members.items() if len(m) > 1}
    slots = defaultdict(list)
    for i, ln in enumerate(lines):
        for j, w in enumerate(ln["words"]):
            for k, c in enumerate(w["word"]):
                canon = collapse_table.get(c)
                if canon in multi:
                    slots[canon].append((i, j, k, c))
    words = [[list(w["word"]) for w in ln["words"]] for ln in lines]
    rng = random.Random(seed)
    for canon in sorted(slots):
        syms = [s[3] for s in slots[canon]]
        rng.shuffle(syms)
        for (i, j, k, _), c in zip(slots[canon], syms):
            words[i][j][k] = c
    return [dict(ln, words=[dict(w, word="".join(ws)) for w, ws in zip(ln["words"], wl)])
            for ln, wl in zip(lines, words)]


def arms(lines: list[dict], mapping: dict, shams=(1, 2, 3)) -> dict[str, list[dict]]:
    table = mapping["collapse_table"]
    out = {"full": lines, "collapsed": represent(lines, table)}
    for s in shams:
        out[f"sham{s}"] = sham_lines(lines, table, s)
    return out
