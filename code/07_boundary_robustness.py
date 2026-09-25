"""Exploratory follow-ups, chosen AFTER the primary frontier run; no retuning.

Separately records subgroup checks, common-support layout contrasts and a shared
model without exact stem identities. These do not replace primary endpoints.
"""
import csv
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

SPEC=importlib.util.spec_from_file_location("frontier",Path(__file__).with_name("06_boundary_frontier.py"))
f=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(f)


def load_predictions():
    rows=list(csv.DictReader((f.OUT/"predictions.csv").open()))
    for r in rows:
        for key in ("loss0","loss1","brier0","brier1","position","correct0","correct1"):
            r[key]=float(r[key])
        r["fold"]=int(r["fold"])
    return rows


def matched_contrast(rows, kind):
    def key(r):
        return tuple(r[k] for k in ("stem","initial","hand","currier","section"))
    a,b=defaultdict(list),defaultdict(list)
    for r in rows:
        if r["kind"] == "ordinary":a[key(r)].append(r)
        if r["kind"] == kind:b[key(r)].append(r)
    shared=set(a)&set(b)
    if not shared:return {"cells":0}
    weighted=[]
    for k in sorted(shared):
        weighted.extend((r,len(b[k])/len(a[k]),0) for r in a[k])
        weighted.extend((r,1.,1) for r in b[k])
    # Difference of context gains: target minus ordinary, standardized to the
    # target's common-support cell distribution. Cluster-resample fixed weights.
    def aggregate(cluster):
        groups=defaultdict(lambda:np.zeros(4))
        for r,w,target in weighted:
            groups[r[cluster]][target*2]+=w*(r["loss0"]-r["loss1"])
            groups[r[cluster]][target*2+1]+=w
        return np.array(list(groups.values()))
    def effect(v):return v[2]/v[3]-v[0]/v[1]
    v=aggregate("folio").sum(axis=0)
    out=dict(cells=len(shared),target_n=sum(len(b[k]) for k in shared),
             ordinary_n=sum(len(a[k]) for k in shared),ordinary_gain=v[0]/v[1],
             target_gain=v[2]/v[3],difference=effect(v))
    for cluster in ("folio","stem"):
        groups=aggregate(cluster);rng=np.random.default_rng(f.SEED);boot=[]
        for _ in range(2000):
            v=groups[rng.integers(len(groups),size=len(groups))].sum(axis=0)
            if v[1]>0 and v[3]>0:boot.append(effect(v))
        out["ci_"+cluster]=np.quantile(boot,[.025,.975]).tolist()
    return out


def main():
    rows=load_predictions()
    results={}
    crossed=[r for r in rows if r["experiment"] == "crossed_stem_folio"]
    results["crossed_subgroups"]={col:{value:f.summary([r for r in crossed if r[col]==value])
                                      for value in sorted({r[col] for r in crossed})}
                                   for col in ("currier","hand","section")}
    results["crossed_minimum_stem_length"]={str(n):f.summary([r for r in crossed if len(f.eva_glyphs(r["stem"]))>=n]) for n in (2,3,4)}
    results["macro_stem_gain"]={}
    for exp in ("crossed_stem_folio","hidden_transfer"):
        subset=[r for r in rows if r["experiment"]==exp]
        bystem=defaultdict(list)
        for r in subset:bystem[r["stem"]].append(r["loss0"]-r["loss1"])
        vals=np.array([np.mean(v) for v in bystem.values()])
        rng=np.random.default_rng(f.SEED)
        boot=[float(np.mean(rng.choice(vals,size=len(vals)))) for _ in range(2000)]
        results["macro_stem_gain"][exp]=dict(stems=len(vals),gain=float(vals.mean()),ci=np.quantile(boot,[.025,.975]).tolist())
    hidden=[r for r in rows if r["experiment"]=="hidden_transfer"]
    # Candidate types may occur on multiple test folds. Keep earliest locus as
    # a deterministic sensitivity, and also bootstrap the original by joined type.
    unique={}
    for r in sorted(hidden,key=lambda r:(r["page"],r["locus"],r["index"])):
        unique.setdefault(r["joined"],r)
    results["hidden_unique_types"]=f.summary(list(unique.values()))
    results["hidden_joined_cluster_ci"]=f.cluster_ci(hidden,"loss0","loss1","joined")
    results["accuracy_gain_ci"]={}
    for exp in ("crossed_stem_folio","hidden_transfer"):
        subset=[r for r in rows if r["experiment"]==exp]
        results["accuracy_gain_ci"][exp]={c:f.cluster_ci(subset,"correct1","correct0",c) for c in ("folio","stem")}
    transfer=[r for r in rows if r["experiment"]=="folio_transfer"]
    results["layout_common_support"]={kind:matched_contrast(transfer,kind) for kind in ("drawing","line","paragraph")}
    # Added after seeing sparse stem+initial models' calibration losses; this
    # is an explicitly exploratory representation ablation, not model selection.
    lines=f.load_lines(f.ROOT/"data/ZL3b-n.txt")
    data=f.observations(lines)
    folds=json.loads((f.OUT/"manifest.json").read_text())["folios"]
    extra=[]
    prior_scores=[]
    for fold in range(5):
        train=[r for r in data if r["kind"]=="ordinary" and folds[r["folio"]]!=fold]
        test=[r for r in data if folds[r["folio"]]==fold]
        base=f.Model(train)
        full=f.Model(train,context=True)
        extra.extend(f.score(test,base.predict(test),full.predict(test),"shared_folio",fold))
        counts=f.Counter(r["terminal"] for r in train)
        prior=np.array([(counts[c]+1)/(len(train)+3) for c in f.CLASSES])
        ordinary_test=[r for r in test if r["kind"]=="ordinary"]
        prior_scores.extend(f.score(ordinary_test,np.tile(prior,(len(ordinary_test),1)),
                                    base.predict(ordinary_test),"prior_reference",fold))
        print('Shared model fold',fold,flush=True)
    f.write_csv(f.OUT/"exploratory_predictions.csv",extra)
    results["shared_folio"]={kind:f.summary([r for r in extra if r["kind"]==kind]) for kind in sorted({r["kind"] for r in extra})}
    results["prior_reference"]=f.summary(prior_scores)
    # Joint follow-up: the identical crossed stem/folio design at non-ordinary
    # boundaries. Stems absent from all ordinary-space training get a stable fold.
    stemfolds=json.loads((f.OUT/"manifest.json").read_text())["stems"]
    def sfold(stem):
        return stemfolds.get(stem,int(hashlib.sha256(stem.encode()).hexdigest()[:8],16)%5)
    joint=[]
    for fold in range(5):
        for stemfold in range(5):
            train=[r for r in data if r["kind"]=="ordinary" and folds[r["folio"]]!=fold and sfold(r["stem"])!=stemfold]
            test=[r for r in data if r["kind"]!="ordinary" and folds[r["folio"]]==fold and sfold(r["stem"])==stemfold]
            if not test:continue
            assert not {r["stem"] for r in train}&{r["stem"] for r in test}
            assert not {r["folio"] for r in train}&{r["folio"] for r in test}
            base=f.Model(train)
            full=f.Model(train,context=True)
            joint.extend(f.score(test,base.predict(test),full.predict(test),"crossed_layout",fold))
        print('Joint layout crossed fold',fold,flush=True)
    f.write_csv(f.OUT/"joint_layout_predictions.csv",joint)
    results["crossed_layout"]={kind:f.summary([r for r in joint if r["kind"]==kind]) for kind in sorted({r["kind"] for r in joint})}
    (f.OUT/"robustness.json").write_text(json.dumps(results,indent=2))
    paths=[*sorted((f.ROOT/"data/frontier/boxes").glob("*.js")),
           f.ROOT/"uv.lock",f.ROOT/"pyproject.toml",Path(__file__).resolve(),
           f.ROOT/"code/test_boundary_frontier.py",f.ROOT/"code/fetch_frontier_coordinates.py"]
    (f.OUT/"supplement_manifest.json").write_text(json.dumps({str(p.relative_to(f.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))
    print(json.dumps(results,indent=2))


if __name__ == "__main__":main()
