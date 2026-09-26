"""Parse v101, infer the v101 -> EVA glyph mapping, and report agreement statistics.

Step 1 of the v101 stage (see V101_PROTOCOL.md for the tests that use it).
Outputs go to results/v101_2026-09-26/:

* mapping.json       per-symbol EVA image, purity, alternatives; merged sets
* agreement.json     word/line agreement v101-vs-ZL, with IT2a-vs-ZL as reference
* line_alignment.csv v101 text line -> ZL locus and ZL descriptor

Run: uv run --locked python code/19_v101_mapping.py   (about 2 minutes)
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import v101

ROOT = v101.ROOT
OUT = ROOT / "results/v101_2026-09-26"
ACCEPT = 0.5          # max normalised edit distance for a word pair to train/score purity
MIN_SET_COUNT = 20    # a symbol needs this many text occurrences to be listed in a merged set


def word_stats(pairs):
    """pairs: (a, b) clean strings already in EVA."""
    n = len(pairs)
    exact = sum(a == b for a, b in pairs)
    ed = sum(v101.edit_distance(a, b) for a, b in pairs)
    ln = sum(max(len(a), len(b)) for a, b in pairs)
    return dict(word_pairs=n, exact_match=exact / n if n else None, char_error_rate=ed / ln if ln else None)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    vlines = v101.load_v101()
    zmeta, zlines = v101.load_ivtff_all(v101.ZL_PATH)
    _, itlines = v101.load_ivtff_all(v101.IT_PATH)
    mp, history = v101.infer_mapping(vlines, zlines, accept=ACCEPT)

    text = [ln for ln in vlines if ln["kind"] == "text"]
    counts_all = Counter(c for ln in vlines for w in ln["words"] for c in w["word"] if c not in v101.UNCERTAIN)
    counts_text = Counter(c for ln in text for w in ln["words"] for c in w["word"] if c not in v101.UNCERTAIN)

    # Final alignment and agreement.
    matched = v101.align_pages(vlines, zlines, mp)
    all_pairs, accepted = [], []
    usage = defaultdict(Counter)
    for vl, zl in matched:
        for a, b, d, _, _ in v101.align_words(vl, zl, mp):
            if not (a["clean"] and b["clean"]):
                continue
            all_pairs.append((v101.transliterate(a["word"], mp), b["word"]))
            if d <= ACCEPT:
                accepted.append((a["word"], b["word"]))
                path = v101.viterbi(a["word"], b["word"], mp)
                if path:
                    for c, s in zip(a["word"], path):
                        usage[c][s] += 1

    # Reference: IT2a vs ZL on identical loci (same word-alignment procedure, no mapping needed).
    itmap = {ln["locus"]: ln for ln in itlines}
    ref_pairs, ref_lines = [], 0
    for zl in zlines:
        it = itmap.get(zl["locus"])
        if it is None:
            continue
        ref_lines += 1
        zw, iw = zl["words"], it["words"]
        cost = lambda i, j: v101.norm_dist(iw[i]["word"], zw[j]["word"])
        for i, j in v101.align_sequences(list(range(len(iw))), list(range(len(zw))), cost, gap=0.6):
            if iw[i]["clean"] and zw[j]["clean"]:
                ref_pairs.append((iw[i]["word"], zw[j]["word"]))

    # Collapsed-to-EVA-class v101 (canonical symbol) transliterates identically by construction;
    # the agreement row for it is therefore the same as the full one and is not repeated.
    zl_text_loci = {z["locus"] for z in zlines if "P" in z["descriptor"]}
    agreement = {
        "v101_text_lines": len(text),
        "v101_label_lines": len(vlines) - len(text),
        "v101_text_lines_aligned_to_zl": len(matched),
        "aligned_to_zl_paragraph_lines": sum(zl["locus"] in zl_text_loci for _, zl in matched),
        "v101_vs_zl_all_aligned_word_pairs": word_stats(all_pairs),
        "v101_vs_zl_accepted_pairs(dist<=0.5)": word_stats([(v101.transliterate(a, mp), b) for a, b in accepted]),
        "reference_it2a_vs_zl_same_loci": dict(lines=ref_lines, **word_stats(ref_pairs)),
        "em_history": history,
    }
    sets = v101.merged_sets(mp, counts_text, MIN_SET_COUNT)
    symbols = {}
    for c, n in sorted(counts_all.items(), key=lambda kv: -kv[1]):
        u = usage.get(c, Counter())
        tot = sum(u.values())
        best = mp.best(c)
        symbols[c] = dict(codepoint=f"U+{ord(c):04X}", count_all=n, count_text=counts_text[c], eva=best,
                          em_prob=round(mp.table.get(c, {}).get(best, 0.0), 4),
                          aligned=tot, purity=round(u[best] / tot, 4) if tot else None,
                          alternatives=[(s, k) for s, k in u.most_common(4) if s != best][:3])
    mapping = {"note": "EVA image = argmax of EM emission table; purity = share of Viterbi alignments "
                       "(accepted word pairs) using that image. Symbols with count_text < "
                       f"{MIN_SET_COUNT} are mapped but excluded from merged-set listing.",
               "symbols": symbols,
               "merged_sets": {k: v for k, v in sorted(sets.items()) if len(v) > 1},
               "single_symbol_classes": {k: v[0] for k, v in sorted(sets.items()) if len(v) == 1},
               "collapse_table": v101.collapse_table(mp, counts_text),
               "emission_table": {c: {s: round(p, 5) for s, p in sorted(row.items(), key=lambda kv: -kv[1])[:6]}
                                  for c, row in mp.table.items()}}
    (OUT / "mapping.json").write_text(json.dumps(mapping, indent=1, ensure_ascii=False))
    (OUT / "agreement.json").write_text(json.dumps(agreement, indent=2))
    with (OUT / "line_alignment.csv").open("w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["v101_locus", "zl_locus", "zl_descriptor", "zl_hand", "zl_language", "distance"])
        for vl, zl in matched:
            d = v101.norm_dist(v101.line_string(vl["words"], lambda w: v101.transliterate(w, mp)),
                               v101.line_string(zl["words"]))
            wr.writerow([vl["locus"], zl["locus"], zl["descriptor"], zl["meta"].get("H", ""),
                         zl["meta"].get("L", ""), round(d, 3)])
    (OUT / "mapping_manifest.json").write_text(json.dumps({
        "script": "code/19_v101_mapping.py", "accept": ACCEPT, "min_set_count": MIN_SET_COUNT,
        "max_emit": v101.MAX_EMIT, "length_prior": v101.LENGTH_PRIOR,
        "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in [v101.V101_PATH, v101.ZL_PATH, v101.IT_PATH, Path(__file__).resolve(),
                             ROOT / "code/v101.py"]}}, indent=2))
    print(json.dumps(agreement, indent=2))
    print(json.dumps(mapping["merged_sets"], ensure_ascii=False))


if __name__ == "__main__":
    main()
