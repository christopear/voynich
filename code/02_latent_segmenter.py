from pathlib import Path
from collections import Counter
import json
import math

from voynich_core import parse_zl3b, select_pages, filter_lines, eva_glyphs, candidate_splits, viterbi_segment

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
pages, lines = parse_zl3b(DATA / "ZL3b-n.txt")
pids = select_pages(pages, section="H", currier="A", hand="1")
page_set = set(pids)
sub = filter_lines(lines, pids)

# Cross-validation benchmark: concatenate genuine adjacent held-out pairs and ask
# the training corpus to locate the missing boundary.
ambiguous = correct = 0
examples = []
for hold in pids:
    train_lines = [x for x in sub if x.page != hold]
    test_lines = [x for x in sub if x.page == hold]
    freq = Counter(w for L in train_lines for w in L.tokens)
    for L in test_lines:
        for i in range(len(L.tokens)-1):
            a,b = L.tokens[i],L.tokens[i+1]
            ga,gb = eva_glyphs(a),eva_glyphs(b)
            if len(ga)<2 or len(gb)<2 or len(ga)+len(gb)>14:
                continue
            if freq[a] < 2 or freq[b] < 2:
                continue
            joined = a+b
            cs = candidate_splits(joined, freq, boundary_bonus=0.75)
            true_k = len(ga)
            if len(cs) < 2 or not any(x["k"] == true_k for x in cs):
                continue
            ambiguous += 1
            correct += cs[0]["k"] == true_k
            if len(examples) < 20:
                examples.append({"hold":hold,"joined":joined,"true":f"{a} · {b}","pred":f"{cs[0]['a']} · {cs[0]['b']}"})

# f3r completely excluded from frequency estimates.
freq = Counter(w for L in sub if L.page != "f3r" for w in L.tokens)
f3 = [L for L in sub if L.page == "f3r"]
f3_out=[]
for L in f3:
    toks=[]
    for w in L.tokens:
        z = viterbi_segment(w, freq, llr_threshold=-2.1654, boundary_bonus=1.0)
        toks.append({"surface":w,"parts":z["parts"],"margin":z["margin"]})
    f3_out.append({"line":L.locus,"tokens":toks})

print(json.dumps({
    "pages":len(pids),
    "ambiguous_missing_space_cases":ambiguous,
    "boundary_accuracy":correct/ambiguous if ambiguous else None,
    "examples":examples,
    "f3r":f3_out,
}, indent=2))
