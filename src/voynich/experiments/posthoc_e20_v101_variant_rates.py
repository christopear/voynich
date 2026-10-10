"""Post hoc descriptive rate tables for the v101 variant sets (not part of the pre-set rules).

Run: uv run --locked python -m voynich.experiments.posthoc_e20_v101_variant_rates
"""
import json
from collections import Counter, defaultdict

from voynich import v101_data as vd
from voynich.experiments import e20_v101_variant_test as vt

SETS = [("p", {"g", "j"}, "j"), ("d", {"8", "7", "6"}, "7"), ("sh", set("235%+!#"), "2"), ("r", set("yxYb"), "x"),
        ("y", set("9("), "("), ("k", set("hW"), "W"), ("f", set("fu"), "u"), ("cph", set("JG"), "G")]


def tab(rows, keyf, minor):
    c = defaultdict(Counter)
    for r in rows:
        c[keyf(r)][r["sym"]] += 1
    out = {}
    for k, v in sorted(c.items(), key=lambda kv: -sum(kv[1].values())):
        n = sum(v.values())
        if n >= 20:
            out[str(k)] = (n, round(v[minor] / n, 3))
    return out


def main():
    lines, mapping = vd.load_corpus()
    coll = vd.represent(lines, mapping["collapse_table"])
    res = {}
    for cls, members, minor in SETS:
        rows = vt.occurrences(lines, coll, members)
        res[cls] = {"minor": minor,
                    "line_first_word": tab(rows, lambda r: (r["wi"] == 0), minor),
                    "paragraph_first_line": tab(rows, lambda r: r["pfl"], minor),
                    "glyph_pos": tab(rows, lambda r: vt.family_features(r, "POS", "collapsed")["gpos"], minor),
                    "next": tab(rows, lambda r: vt.ctx(r, "collapsed")[2], minor),
                    "prev": tab(rows, lambda r: vt.ctx(r, "collapsed")[1], minor),
                    "hand": tab(rows, lambda r: r["hand"], minor),
                    "language": tab(rows, lambda r: r["lang"], minor)}
    (vd.OUT / "variant_posthoc_rates.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    for k in ("p", "d", "sh", "f"):
        print(k, json.dumps(res[k], ensure_ascii=False))


if __name__ == "__main__":
    main()
