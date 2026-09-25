from pathlib import Path
from collections import Counter
import json
import re

from voynich_core import (
    parse_zl3b, select_pages, filter_lines, conservative_normalizer,
    prefix_remainder_lattices, context_vectors, cosine_counts, eva_glyphs
)

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
pages,lines=parse_zl3b(DATA/"ZL3b-n.txt")
pids=select_pages(pages,section="H",currier="A",hand="1")
sub=filter_lines(lines,pids)
surface=[w for L in sub for w in L.tokens]
normalize=conservative_normalizer(surface)
normalized=[normalize(w) for w in surface]

lattices=prefix_remainder_lattices(normalized,min_form_freq=5,min_shared_remainders=5,eva=True)
ctx=context_vectors(normalized,top_context=100)
freq=Counter(normalized)

# Add median contextual similarity for each lattice.
for L in lattices:
    sims=[]
    for rem,a,b in L["examples"]:
        sims.append(cosine_counts(ctx[a],ctx[b]))
    sims.sort()
    L["median_context_cosine"] = sims[len(sims)//2] if sims else None
    L["examples"] = [
        {"remainder":r,"a":a,"b":b,"fa":freq[a],"fb":freq[b],"cosine":cosine_counts(ctx[a],ctx[b])}
        for r,a,b in L["examples"][:12]
    ]

print(json.dumps({
    "surface_types":len(set(surface)),
    "normalized_types":len(set(normalized)),
    "top_lattices":lattices[:30],
},indent=2))
