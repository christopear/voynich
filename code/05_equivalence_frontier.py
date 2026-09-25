"""Starter experiment for the next research frontier.

Goal:
1. Calibrate a pairwise 'same hidden state?' classifier on Naibbe, where hidden
   plaintext labels are known.
2. Features must be structural/ciphertext-only.
3. Freeze the model and apply it to Voynich.

This script exports candidate pairwise features rather than fitting a specific ML
model, so Codex can iterate without baking in one classifier choice.
"""
from pathlib import Path
from collections import Counter
import csv

from voynich_core import context_vectors, cosine_counts, eva_glyphs

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
OUT=ROOT/"results"/"naibbe_pair_features.csv"

def flat(path):
    return Path(path).read_text(encoding="utf-8").lower().split()

cipher=flat(DATA/"naibbe_cipher_pre.txt")
plain=flat(DATA/"naibbe_plain_units.txt")
assert len(cipher)==len(plain)

freq=Counter(cipher)
labels={}
for c,p in zip(cipher,plain):
    labels.setdefault(c,Counter())[p]+=1
label={c:d.most_common(1)[0][0] for c,d in labels.items()}
ctx=context_vectors(cipher,top_context=200)

types=[w for w,n in freq.items() if n>=20]
rows=[]
for i,a in enumerate(types):
    ga=eva_glyphs(a)
    for b in types[i+1:]:
        gb=eva_glyphs(b)
        # Structural features only; no plaintext content is used below.
        same_remainder_2 = len(ga)>2 and len(gb)>2 and ga[2:]==gb[2:]
        same_prefix_2 = len(ga)>2 and len(gb)>2 and ga[:2]==gb[:2]
        edit_len = abs(len(ga)-len(gb))
        common_suffix=0
        while common_suffix<min(len(ga),len(gb)) and ga[-1-common_suffix]==gb[-1-common_suffix]:
            common_suffix+=1
        rows.append({
            "a":a,"b":b,
            "freq_a":freq[a],"freq_b":freq[b],
            "context_cosine":cosine_counts(ctx[a],ctx[b]),
            "same_remainder_after_2":int(same_remainder_2),
            "same_prefix_2":int(same_prefix_2),
            "glyph_len_diff":edit_len,
            "common_suffix_units":common_suffix,
            # Label is present only for positive-control training/evaluation.
            "same_hidden_plaintext":int(label[a]==label[b]),
        })

OUT.parent.mkdir(exist_ok=True)
with OUT.open("w",newline="",encoding="utf-8") as fh:
    wr=csv.DictWriter(fh,fieldnames=rows[0].keys())
    wr.writeheader();wr.writerows(rows)
print(f"Wrote {len(rows):,} pair rows to {OUT}")
print("Recommended next step: grouped cross-validation by plaintext label / cipher type, then freeze features+hyperparameters before applying to Voynich.")
