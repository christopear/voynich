"""Forward word-code screen with disjoint homophones, frozen chapter transfer."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
from voynich.experiments.e06_boundary_frontier import load_lines
from voynich.experiments.e27_unit_association import association, page_tokens, sha
from voynich.laboratory.manifest import environment
from voynich.paths import ROOT

GRID=((1.,),(.9,.1),(.75,.25),(.5,.5),(.8,.1,.1),(.6,.2,.2),(1/3,1/3,1/3))
SCALES=np.array([.05,.04,.05,.05])


def save(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')


def new_slots(excluded):
    # The old page helper restricts to H/B; explicitly admit starred-text pages here.
    lines=load_lines(ROOT/'data/ZL3b-n.txt')
    mapped=[]
    for line in lines:
        if line['meta'].get('I')=='S':
            mapped.append(dict(line,meta={**line['meta'],'I':'B'}))
        elif line['meta'].get('I')=='H':mapped.append(line)
    pages=page_tokens(mapped);chosen=[];seen=set(excluded);counts=Counter()
    for page,rows in pages.items():
        section='S' if rows[0]['section']=='B' else 'H'
        if rows[0]['folio'] in seen or len(rows)<64 or counts[section]>=8:continue
        chosen.extend([{**r,'section':section} for r in rows[:64]])
        seen.add(rows[0]['folio']);counts[section]+=1
    if counts!={'H':8,'S':8}:raise ValueError(f'insufficient new pages {counts}')
    return chosen


def it_slots(template):
    lines=load_lines(ROOT/'data/mechanisms/IT2a-n.txt')
    wanted={r['page']:r['section'] for r in template}
    mapped=[dict(ln,meta={**ln['meta'],'L':'B','I':'H'}) for ln in lines if ln['page'] in wanted]
    pages=page_tokens(mapped);out=[]
    for page,section in wanted.items():
        if len(pages.get(page,[]))<64:raise ValueError('IT page too short: '+page)
        out.extend([{**r,'section':section} for r in pages[page][:64]])
    return out


def source_panels(chapters):
    eligible=[c for c in chapters if len(c['words'])>=64]
    available=eligible[max(1,len(eligible)//5):];cut=len(available)//2
    out=[]
    for split,pool,seeds in [('development',available[:cut],(7,19)),('validation',available[cut:],(31,43))]:
        for seed in seeds:
            rng=np.random.default_rng(seed);selected=[pool[i] for i in rng.choice(len(pool),16,replace=False)]
            words=[];spans=[]
            for c in selected:
                start=int(rng.integers(len(c['words'])-63));words+=c['words'][start:start+64]
                spans.append({'chapter':c['id'],'start':start,'stop':start+64})
            out.append(dict(split=split,seed=seed,words=words,spans=spans))
    return out


def make_key(words, k):
    vocabulary=sorted(set(words));permutation=np.random.default_rng(4242+k).permutation(len(vocabulary)*k)
    encode={w:[str(int(n)) for n in permutation[i*k:(i+1)*k]] for i,w in enumerate(vocabulary)}
    decode={c:w for w,codes in encode.items() for c in codes}
    return encode,decode


def encrypt(words,key,probabilities,seed):
    choices=np.searchsorted(np.cumsum(probabilities),np.random.default_rng(seed).random(len(words)),side='right')
    return [key[w][int(j)] for w,j in zip(words,choices)]


def metrics(tokens, slots):
    a=association(tokens,slots,'section');b=association(tokens,slots,'roles')
    counts=Counter(tokens);n=len(tokens)
    adjacent=[i for i in range(1,n) if slots[i]['locus']==slots[i-1]['locus'] and slots[i]['start']==slots[i-1]['end']+1]
    return dict(ttr=len(counts)/n,top10=sum(c for _,c in counts.most_common(10))/n,
        hapax=sum(c==1 for c in counts.values())/len(counts),
        repeat=sum(tokens[i]==tokens[i-1] for i in adjacent)/max(1,len(adjacent)),
        section=a,roles=b)


def vector(m):return np.array([m['ttr'],m['top10'],m['section']['excess'],m['roles']['excess']])
def distance(a,b):return float(np.max(np.abs(np.asarray(a)-np.asarray(b))/SCALES))


def select(target, records):
    candidates=[]
    for index in range(len(GRID)):
        rr=[r for r in records if r['configuration']==index]
        median=np.median([vector(r['metrics']) for r in rr],axis=0)
        candidates.append(dict(configuration=index,distance=distance(median,target),median=median.tolist(),
                               signed_residual=(median-target).tolist()))
    return min(candidates,key=lambda r:(r['distance'],r['configuration'])),candidates


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    previous=ROOT/'results/unit_association_2026-10-09'
    arms=json.loads((previous/'manuscript_slots.json').read_text())
    source=json.loads((previous/'prepared_sources.json').read_text())
    original=arms['split'];additional=new_slots({r['folio'] for r in original})
    layouts={'ZL_original':original,'ZL_joined':arms['join'],'IT_original':it_slots(original),
             'ZL_additional':additional,'IT_additional':it_slots(additional)}
    save(output/'slots.json',layouts)
    paths=[previous/'manuscript_slots.json',previous/'prepared_sources.json',ROOT/'data/ZL3b-n.txt',
           ROOT/'data/mechanisms/IT2a-n.txt',ROOT/'docs/protocols/WORD_HOMOPHONES_2026-10-09.md',Path(__file__)]
    save(output/'manifest.json',dict(environment=environment(ROOT),hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}))
    records=[];keys={};panels={};calibration=[]
    for name in ('cucina','celsus','pliny'):
        panels[name]=source_panels(source[name])
        vocabulary=[w for c in source[name] for w in c['words']]
        keys[name]={str(k):make_key(vocabulary,k)[0] for k in (1,2,3)}
        for panel in panels[name]:
            slots=original if panel['split']=='development' else additional
            for index,probabilities in enumerate(GRID):
                key=keys[name][str(len(probabilities))];decoder={c:w for w,cs in key.items() for c in cs}
                for seed in range(101,107):
                    tokens=encrypt(panel['words'],key,probabilities,seed)
                    assert [decoder[c] for c in tokens]==panel['words']
                    records.append(dict(source=name,split=panel['split'],passage_seed=panel['seed'],encoding_seed=seed,
                        configuration=index,metrics=metrics(tokens,slots),tokens=tokens,roundtrip=True))
            print(name,panel['split'],panel['seed'],'complete',flush=True)
            if name=='cucina' and panel['seed']==7:
                reference=records.copy()
                for index,probabilities in enumerate(GRID):
                    key=keys[name][str(len(probabilities))]
                    for seed in (901,902):
                        target=vector(metrics(encrypt(panel['words'],key,probabilities,seed),slots))
                        best,_=select(target,reference)
                        calibration.append(dict(configuration=index,seed=seed,selected=best['configuration'],distance=best['distance']))
                passed=sum(r['distance']<=1 for r in calibration)
                save(output/'calibration.json',dict(passed=passed,total=14,records=calibration))
                if passed<12:raise AssertionError('synthetic neighbourhood calibration failed')
    save(output/'codebooks.json',keys);save(output/'source_panels.json',panels)
    targets={name:metrics([r['word'] for r in slots],slots) for name,slots in layouts.items()}
    comparisons={}
    for name in panels:
        development=[r for r in records if r['source']==name and r['split']=='development']
        best,grid=select(vector(targets['ZL_original']),development)
        tests={}
        for target_name,target in targets.items():
            split='validation' if target_name.endswith('additional') else 'development'
            rr=[r for r in records if r['source']==name and r['split']==split and r['configuration']==best['configuration']]
            vals=[dict(passage_seed=r['passage_seed'],encoding_seed=r['encoding_seed'],distance=distance(vector(r['metrics']),vector(target)),
                       residual=(vector(r['metrics'])-vector(target)).tolist()) for r in rr]
            tests[target_name]=dict(joint_hits=sum(r['distance']<=1 for r in vals),total=len(vals),draws=vals)
        comparisons[name]=dict(selected=best,grid=grid,tests=tests)
    save(output/'evidence.json',dict(grid=GRID,scales=SCALES.tolist(),records=records,targets=targets,comparisons=comparisons,
                                   status='descriptive forward-model screen; no key recovery or readings'))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'results/word_homophones_2026-10-09')
    run(p.parse_args().output)


if __name__=='__main__':main()
