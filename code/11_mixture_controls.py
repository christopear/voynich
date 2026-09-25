"""Exploratory open-set challenge after primary recovery: untrained mixtures.

Pure mechanisms remain the only trained labels. Blocks alternate between two
independently generated streams, so a pure-class assignment is not a true label.
This checks rejection, not an information-theoretic identifiability theorem.
"""
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
import mechanism_models as m

SPEC=importlib.util.spec_from_file_location('bench',Path(__file__).with_name('09_mechanism_benchmark.py'))
b=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(b)


def main():
    out=b.OUT;result=json.loads((out/'benchmark_summary.json').read_text())
    simulations=json.loads((out/'simulation_features.json').read_text())
    manifest=json.loads((out/'benchmark_manifest.json').read_text())
    lines=b.f.load_lines(m.ROOT/'data/ZL3b-n.txt')
    train=[ln for ln in lines if ln['meta'].get('L')=='B' and ln['folio'] in manifest['train_folios']]
    test=[ln for ln in lines if ln['meta'].get('L')=='B' and ln['folio'] in manifest['test_folios']]
    model=m.Training(train);encoder=m.Encoder(m.ROOT/'data/mechanisms/naibbe_tables.csv')
    plain=m.clean_plain((m.ROOT/'data/latin_alfonsi.txt').read_text());plain=plain[len(plain)//2:]
    forest=RandomForestClassifier(n_estimators=300,min_samples_leaf=2,max_features='sqrt',random_state=8221,n_jobs=1)
    forest.fit(b.matrix(simulations),[r['mechanism'] for r in simulations])
    controls=[];n=sum(len(ln['words']) for ln in test)
    for block in (8,64):
        for seed in range(101000,101006):
            a,aa=m.generate(model,encoder,plain,n,result['best']['assembly'],seed)
            e,ea=m.generate(model,encoder,plain,n,result['best']['encoding'],seed+1000)
            rng=random.Random(seed+block);tokens=[];from_a=0
            for start in range(0,n,block):
                select_a=rng.random()<.5;end=min(n,start+block)
                tokens.extend((a if select_a else e)[start:end]);from_a+=(end-start)*select_a
            fp=m.fingerprint(m.apply_template(test,tokens))
            row=dict(fp,block=block,seed=seed,assembly_fraction=from_a/n)
            row['centroid']=b.predict(b.centroid_fit(simulations),[fp])[0]
            p=forest.predict_proba(b.matrix([fp]))[0]
            row['forest']=dict(prediction=str(forest.classes_[p.argmax()]),max_score=float(p.max()))
            controls.append(row)
    report=dict(status='Exploratory hybrid challenge chosen after primary recovery. These mixtures are outside the three pure labels, not outside all conceivable mechanisms.',
                n=len(controls),centroid_rejected=sum(r['centroid']['rejected'] for r in controls),
                forest_score_at_least_08=sum(r['forest']['max_score']>=.8 for r in controls),controls=controls,
                code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'mixture_controls.json').write_text(json.dumps(report,indent=2))
    print({k:v for k,v in report.items() if k!='controls'})


if __name__=='__main__':main()
