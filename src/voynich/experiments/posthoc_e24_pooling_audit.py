"""Sufficient audit of old ZL conjunction verdicts, without rerunning full grids."""
import argparse
from collections import Counter,OrderedDict
import json
from pathlib import Path
import random
import numpy as np
from voynich import cipher_families as cf, mechanism_models as mm
from voynich.experiments.e24_cipher_family_benchmark import config_stats
from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e28_word_homophones import save
from voynich.laboratory.manifest import environment
from voynich.paths import ROOT

MODES=('first','identity','all')


def page_mi(lines,mode):
    rows=[(w['word'],ln['page']) for ln in lines for w in ln['words'] if w['clean']]
    counts=Counter(t for t,_ in rows)
    if mode=='first':keep={w for w,_ in counts.most_common(200)}
    elif mode=='identity':keep=set(sorted(counts,key=lambda w:(-counts[w],w))[:200])
    elif mode=='all':keep=set(counts)
    else:raise ValueError(mode)
    tokens=cf.encode([(0,w) if w in keep else (1,'') for w,_ in rows])
    pages=cf.encode([p for _,p in rows])
    return cf.corrected(tokens,pages,None,np.random.default_rng(cf.FP_SEED))


def bootstrap(lines):
    pages=OrderedDict()
    for ln in lines:pages.setdefault(ln['page'],[]).append(ln)
    rng=random.Random(20260926);out={m:[] for m in MODES}
    for _ in range(200):
        picked=[rng.choice(list(pages)) for _ in pages]
        laid=[dict(ln,page=f'{p}#{j}') for j,p in enumerate(picked) for ln in pages[p]]
        for m in MODES:out[m].append(page_mi(laid,m))
    return {m:float(np.std(v,ddof=1)) for m,v in out.items()}


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    old=ROOT/'results/cipher_families_2026-09-26'
    runs=json.loads((old/'step_a_runs.json').read_text());oldtargets=json.loads((old/'step_a_verdicts.json').read_text())
    w1,w2,train=cf.currier_b_windows();training=mm.Training(train)
    configs={cf.config_key(c):c for c in cf.configurations()};result={};reproduced=0
    for win,lines in [('W1',w1),('W2',w2)]:
        stats,families=config_stats(runs,win);target=oldtargets['targets']['ZL_'+win];sd=oldtargets['target_bootstrap_sd']['ZL_'+win]
        tv={m:page_mi(lines,m) for m in MODES};tsd=bootstrap(lines)
        assert abs(tv['first']-target['P6_page_mi'])<1e-12
        assert abs(tsd['first']-sd['P6_page_mi'])<1e-12
        cells=[]
        for key,(mean,sigma) in stats.items():
            shape_z={n:float(abs(target[n]-mean[i])/np.sqrt(sigma[i]**2+sd[n]**2)) for i,n in enumerate(cf.PRIMARY[:4])}
            cell=dict(key=key,family=families[key],unchanged_shape_z=shape_z)
            if max(shape_z.values())>3:
                cell['reason']='fails unchanged P1–P4';cell['excluded']={m:True for m in MODES}
            else:
                draws=[]
                for seed in (1,2,3,4,5,6):
                    laid,_=cf.simulate(configs[key],lines,seed,training)
                    values={m:page_mi(laid,m) for m in MODES}
                    oldrow=next(r for r in runs if r['key']==key and r['window']==win and r['seed']==seed)
                    assert abs(values['first']-oldrow['P6_page_mi'])<1e-12
                    draws.append(dict(seed=seed,**values));reproduced+=1
                z={m:float(abs(tv[m]-np.mean([r[m] for r in draws]))/np.sqrt(tsd[m]**2+np.std([r[m] for r in draws],ddof=1)**2)) for m in MODES}
                cell.update(reason='shape survived; recomputed P6',draws=draws,p6_z=z,excluded={m:z[m]>3 for m in MODES})
                print(win,key,cell['excluded'],flush=True)
            cells.append(cell)
        result[win]=dict(target=tv,target_bootstrap_sd=tsd,cells=cells,
                        all_cells_excluded={m:all(c['excluded'][m] for c in cells) for m in MODES})
        save(output/f'{win}.json',result[win])
    paths=[old/'step_a_runs.json',old/'step_a_verdicts.json',Path(__file__),ROOT/'docs/protocols/HISTORICAL_POOLING_AUDIT_2026-10-09.md']
    save(output/'evidence.json',dict(windows=result,reproduced_simulations=reproduced,environment=environment(ROOT),
        input_hashes={str(p.relative_to(ROOT)):sha(p) for p in paths},
        scope='Sufficient audit of original ZL two-window verdicts only; P5/P7–P9 changes not measured'))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'results/historical_pooling_audit_2026-10-09')
    run(p.parse_args().output)


if __name__=='__main__':main()
