"""Locked family/transcription/glyph robustness gate; see MECHANISM_PROTOCOL.md."""
import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

SPEC=importlib.util.spec_from_file_location('frontier',Path(__file__).with_name('06_boundary_frontier.py'))
f=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(f)
ROOT=f.ROOT
OUT=ROOT/'results/mechanisms_2026-09-24'
ORIGINAL_GLYPHS=f.eva_glyphs


def family(stem):
    core=re.sub(r'^q?o?', '',stem)
    return re.sub(r'i+','i',re.sub(r'e+','e',core)) or '<empty>'


def glyphs(word,mode):
    if mode=='characters':return list(word)
    if mode=='minims':
        return re.findall(r'cth|ckh|cph|cfh|ch|sh|ee|ii|.',word)
    return ORIGINAL_GLYPHS(word)


def run_cross(rows,folios,familyfolds,mode='original',drop=0):
    f.eva_glyphs=lambda w:glyphs(w,mode)
    predictions=[];audit=[]
    for fold in range(5):
        ft=[r for r in rows if folios[r['folio']]!=fold]
        counts=Counter(r['family'] for r in ft)
        excluded={k for k,n in sorted(counts.items(),key=lambda kv:(-kv[1],kv[0]))[:drop]}
        for ff in range(5):
            train=[r for r in ft if familyfolds[r['family']]!=ff and r['family'] not in excluded]
            test=[r for r in rows if folios[r['folio']]==fold and familyfolds[r['family']]==ff and r['family'] not in excluded]
            if not test:continue
            assert not {r['family'] for r in train}&{r['family'] for r in test}
            assert not {r['folio'] for r in train}&{r['folio'] for r in test}
            base=f.Model(train);full=f.Model(train,context=True)
            predictions.extend(f.score(test,base.predict(test),full.predict(test),f'{mode}_drop{drop}',fold))
            audit.append(dict(fold=fold,family_fold=ff,train_n=len(train),test_n=len(test),excluded=sorted(excluded)))
        print('gate',mode,'drop',drop,'folio',fold,flush=True)
    f.eva_glyphs=ORIGINAL_GLYPHS
    return predictions,audit


def summarize(rows):
    s=f.summary(rows)
    if rows:s['gain_ci_family']=f.cluster_ci(rows,'loss0','loss1','family')
    return s


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    paths={'ZL':ROOT/'data/ZL3b-n.txt','IT':ROOT/'data/mechanisms/IT2a-n.txt'}
    data={name:[dict(r,family=family(r['stem'])) for r in f.observations(f.load_lines(path)) if r['kind']=='ordinary'] for name,path in paths.items()}
    folios=json.loads((ROOT/'results/frontier_2026-09-24/manifest.json').read_text())['folios']
    # Existing physical folds are frozen. Exclude any alternative-only folios.
    data={name:[r for r in rows if r['folio'] in folios] for name,rows in data.items()}
    families=f.assign_folds(r['family'] for rows in data.values() for r in rows)
    common={r['locus'] for r in data['ZL']}&{r['locus'] for r in data['IT']}
    summary={};allpred=[];allaudit={}
    for source,mode,drop in [('ZL','original',0),('ZL','characters',0),('ZL','minims',0),('IT','original',0),('ZL','original',5)]:
        # Recalculate initials when the glyph alphabet changes.
        rows=[dict(r,initial=glyphs(r['right'],mode)[0]) for r in data[source]]
        pred,audit=run_cross(rows,folios,families,mode,drop)
        name=f'{source}_{mode}_drop{drop}'
        for r in pred:r['experiment']=name
        allpred.extend(pred);allaudit[name]=audit
        summary[name]=dict(all=summarize(pred),currier={c:summarize([r for r in pred if r['currier']==c]) for c in ('A','B')},common_loci=summarize([r for r in pred if r['locus'] in common]))
        f.write_csv(OUT/'gate_predictions.csv',allpred)
        (OUT/'gate_summary.json').write_text(json.dumps(summary,indent=2))
        print(name,summary[name]['all']['gain_bits'],flush=True)
    inputs=[*paths.values(),ROOT/'MECHANISM_PROTOCOL.md',Path(__file__).resolve(),ROOT/'code/06_boundary_frontier.py']
    (OUT/'gate_manifest.json').write_text(json.dumps(dict(folios=folios,families=families,audit=allaudit,hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}),indent=2))


if __name__=='__main__':main()
