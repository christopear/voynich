from pathlib import Path
from collections import Counter
import json
import math

from voynich_core import eva_glyphs, candidate_splits

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"

def token_lines(path):
    return [x.strip().split() if x.strip() else [] for x in Path(path).read_text(encoding="utf-8").splitlines()]

pre=token_lines(DATA/"naibbe_cipher_pre.txt")
post=token_lines(DATA/"naibbe_cipher_respaced.txt")
plain=token_lines(DATA/"naibbe_plain_units.txt")

# Align post-respacing written token to one or more original pre-respacing tokens.
aligned=[]
errors=[]
for li,(a,b) in enumerate(zip(pre,post)):
    i=0
    for w in b:
        joined="";parts=[]
        while i<len(a) and len(joined)<len(w):
            joined += a[i]; parts.append(a[i]); i+=1
        if joined != w:
            errors.append((li,w,joined,parts));break
        aligned.append({"line":li,"w":w,"parts":parts})

comp=[x for x in aligned if len(x["parts"])>1]

# 3-fold line-held-out frequency model. Score exact one-boundary compounds.
loc_n=loc_ok=0
for fold in range(3):
    train=[x for x in aligned if x["line"]%3 != fold]
    freq=Counter(x["w"] for x in train)
    for r in aligned:
        if r["line"]%3 != fold or len(r["parts"])!=2:
            continue
        cs=candidate_splits(r["w"],freq,boundary_bonus=0.0)
        if not cs:
            continue
        true_k=len(eva_glyphs(r["parts"][0]))
        if not any(x["k"]==true_k for x in cs):
            continue
        loc_n+=1;loc_ok+=cs[0]["k"]==true_k

# Align pre-respacing cipher token to known plaintext unit. Lines are one-to-one.
plain_map={}
freq_pre=Counter()
for c_line,p_line in zip(pre,plain):
    if len(c_line)!=len(p_line):
        continue
    for c,p in zip(c_line,p_line):
        freq_pre[c]+=1
        plain_map.setdefault(c,Counter())[p]+=1

def top_plain(w):
    return plain_map[w].most_common(1)[0][0] if w in plain_map else None

okot=[]
for c,n in freq_pre.items():
    if not c.startswith("ok") or n<5 or len(c)<3:
        continue
    rem=c[2:]
    ot="ot"+rem
    if freq_pre[ot] >= 5:
        okot.append({
            "remainder":rem,
            "ok":c,"ot":ot,
            "f_ok":n,"f_ot":freq_pre[ot],
            "plain_ok":top_plain(c),"plain_ot":top_plain(ot),
            "same_plain":top_plain(c)==top_plain(ot),
        })
weighted_num=sum(min(x["f_ok"],x["f_ot"]) for x in okot if x["same_plain"])
weighted_den=sum(min(x["f_ok"],x["f_ot"]) for x in okot)

print(json.dumps({
    "alignment_errors":len(errors),
    "post_tokens":len(aligned),
    "compound_tokens":len(comp),
    "compound_pct":100*len(comp)/len(aligned),
    "two_part":sum(len(x["parts"])==2 for x in comp),
    "boundary_localization_n":loc_n,
    "boundary_localization_accuracy":loc_ok/loc_n if loc_n else None,
    "okot_pairs":len(okot),
    "okot_same_plain_type_pct":100*sum(x["same_plain"] for x in okot)/len(okot),
    "okot_weighted_same_plain_pct":100*weighted_num/weighted_den,
    "okot_examples":sorted(okot,key=lambda x:x["f_ok"]+x["f_ot"],reverse=True)[:40],
},indent=2))
