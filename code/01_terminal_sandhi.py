from pathlib import Path
from collections import Counter
import json

from voynich_core import (
    parse_zl3b, select_pages, filter_lines, line_position_stats,
    terminal_records, stem_preserving_terminal_permutation_test
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
pages, lines = parse_zl3b(DATA / "ZL3b-n.txt")

# Main controlled subset.
pids = select_pages(pages, section="H", currier="A", hand="1")
subset = filter_lines(lines, pids)

# Same-stem m versus n/l/r siblings.
pos = line_position_stats(subset)
rows = []
for w, z in pos.items():
    if not w.endswith("m") or len(w) < 2:
        continue
    stem = w[:-1]
    sibs = [stem + x for x in "nlr" if stem + x in pos]
    if not sibs:
        continue
    sib_n = sum(pos[s]["n"] for s in sibs)
    sib_last = sum(pos[s]["last"] for s in sibs)
    rows.append({
        "m": w,
        "m_n": z["n"],
        "m_last_rate": z["last_rate"],
        "siblings": sibs,
        "sib_n": sib_n,
        "sib_last_rate": sib_last / sib_n if sib_n else None,
    })

within = stem_preserving_terminal_permutation_test(terminal_records(lines, across_line=False))
across = stem_preserving_terminal_permutation_test(terminal_records(lines, across_line=True))
within_sub = stem_preserving_terminal_permutation_test(terminal_records(subset, across_line=False))
across_sub = stem_preserving_terminal_permutation_test(terminal_records(subset, across_line=True))

print(json.dumps({
    "herbal_A_hand1_pages": len(pids),
    "m_families_top": sorted(rows, key=lambda x: x["m_n"], reverse=True)[:30],
    "terminal_next_initial": {
        "full_within_line": within,
        "full_across_line": across,
        "herbal_A_hand1_within_line": within_sub,
        "herbal_A_hand1_across_line": across_sub,
    },
}, indent=2))
