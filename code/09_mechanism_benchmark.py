"""Calibrate specified generators, test withheld diagnostics and recovery."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

import mechanism_models as m

SPEC=importlib.util.spec_from_file_location('gate',Path(__file__).with_name('08_robustness_gate.py'))
g=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(g)
f=g.f;ROOT=f.ROOT;OUT=ROOT/'results/mechanisms_2026-09-24'


def matrix(rows):return np.array([[r[k] for k in m.DIAGNOSTICS] for r in rows])


def centroid_fit(rows):
    x=matrix(rows);sd=x.std(axis=0);sd=np.maximum(sd,1e-6)
    centres={c:np.mean(x[[r['mechanism']==c for r in rows]],axis=0) for c in m.CLASSES}
    threshold={c:float(np.quantile(np.mean(((x[[r['mechanism']==c for r in rows]]-centres[c])/sd)**2,axis=1),.95)) for c in m.CLASSES}
    return sd,centres,threshold


def predict(model,rows):
    sd,centres,threshold=model;out=[]
    for r,x in zip(rows,matrix(rows)):
        distances={c:float(np.mean(((x-centres[c])/sd)**2)) for c in m.CLASSES}
        closest=min(distances,key=distances.get)
        compatible=[c for c in m.CLASSES if distances[c]<=threshold[c]]
        out.append(dict(truth=r.get('mechanism','Voynich'),closest=closest,compatible=compatible,
                        distances=distances,rejected=not compatible))
    return out


def recovery(rows,mode):
    predictions=[]
    if mode=='parameters':splits=[([r for r in rows if r['level']!=k],[r for r in rows if r['level']==k],str(k)) for k in range(3)]
    else:splits=[([r for r in rows if r['source']==a],[r for r in rows if r['source']==b],a+'->'+b) for a,b in [('latin','italian'),('italian','latin')]]
    for train,test,label in splits:
        for r,p in zip(test,predict(centroid_fit(train),test)):
            predictions.append(dict(p,split=label,seed=r['seed'],level=r['level'],source=r['source']))
    conf={c:{p:0 for p in m.CLASSES} for c in m.CLASSES}
    for p in predictions:conf[p['truth']][p['closest']]+=1
    return dict(n=len(predictions),accuracy=float(np.mean([p['truth']==p['closest'] for p in predictions])),
                rejection_rate=float(np.mean([p['rejected'] for p in predictions])),confusion=conf,
                by_split={s:float(np.mean([p['truth']==p['closest'] for p in predictions if p['split']==s])) for s in sorted({p['split'] for p in predictions})},predictions=predictions)


def corpus_hash(words):return hashlib.sha256('\n'.join(words).encode()).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lines=f.load_lines(ROOT/'data/ZL3b-n.txt')
    folios=json.loads((ROOT/'results/frontier_2026-09-24/manifest.json').read_text())['folios']
    b=[ln for ln in lines if ln['meta'].get('L')=='B']
    train=[ln for ln in b if folios[ln['folio']]<3]
    test=[ln for ln in b if folios[ln['folio']]>=3]
    assert not {ln['folio'] for ln in train}&{ln['folio'] for ln in test}
    training=m.Training(train);encoder=m.Encoder(ROOT/'data/mechanisms/naibbe_tables.csv')
    plain={name:m.clean_plain((ROOT/path).read_text()) for name,path in [('latin','data/latin_alfonsi.txt'),('italian','data/italian_dante.txt')]}
    ntrain=sum(len(ln['words']) for ln in train);ntest=sum(len(ln['words']) for ln in test)
    target=m.fingerprint(train);observed=m.fingerprint(test)
    configs=list(m.configurations());cal=[]
    print('Benchmark train slots',ntrain,'test slots',ntest,'plain lengths',{k:len(v) for k,v in plain.items()},flush=True)
    for ci,config in enumerate(configs):
        for replicate in range(2):
            seed=61000+ci*100+replicate
            words,audit=m.generate(training,encoder,plain['latin'][:len(plain['latin'])//2],ntrain,config,seed)
            fp=m.fingerprint(m.apply_template(train,words))
            cal.append(dict(config,**fp,seed=seed,replicate=replicate,distance=m.calibration_distance(fp,target),audit=audit,corpus_sha=corpus_hash(words)))
        print('calibration',config,'mean distance',np.mean([r['distance'] for r in cal[-2:]]),flush=True)
    scores=[]
    for config in configs:
        subset=[r for r in cal if all(r[k]==config[k] for k in config)]
        scores.append(dict(config,mean_distance=float(np.mean([r['distance'] for r in subset]))))
    best={c:min([r for r in scores if r['mechanism']==c],key=lambda r:r['mean_distance']) for c in m.CLASSES}
    (OUT/'calibration.json').write_text(json.dumps(dict(target=target,observed=observed,scores=scores,best=best,runs=cal),indent=2))
    simulations=[]
    for ci,config in enumerate(configs):
        for si,(source,text) in enumerate(plain.items()):
            for replicate in range(3):
                seed=71000+ci*100+si*10+replicate
                words,audit=m.generate(training,encoder,text[len(text)//2:],ntest,config,seed)
                fp=m.fingerprint(m.apply_template(test,words))
                simulations.append(dict(config,**fp,source=source,replicate=replicate,seed=seed,audit=audit,corpus_sha=corpus_hash(words)))
        print('recovery simulations',config,flush=True)
        (OUT/'simulation_features.json').write_text(json.dumps(simulations,indent=2))
    result=dict(train_tokens=len(training.words),train_slots=ntrain,test_slots=ntest,test_tokens=observed['tokens'],
                test_folios=len({ln['folio'] for ln in test}),encoder_units=len(encoder.options),
                encoder_cipher_types=len(encoder.reverse),calibration_scales=m.CALIBRATION_SCALES,
                diagnostics=m.DIAGNOSTICS,best=best,observed=observed,
                recovery_parameters=recovery(simulations,'parameters'),recovery_plaintext=recovery(simulations,'plaintext'))
    result['voynich_compatibility']=predict(centroid_fit(simulations),[observed])[0]
    result['synthetic_distance_thresholds']=centroid_fit(simulations)[2]
    result['best_model_predictions']={}
    for mechanism,config in best.items():
        ss=[r for r in simulations if r['mechanism']==mechanism and r['level']==config['level'] and r['coupling']==config['coupling']]
        result['best_model_predictions'][mechanism]={k:dict(mean=float(np.mean([r[k] for r in ss])),minimum=min(r[k] for r in ss),maximum=max(r[k] for r in ss),observed=observed[k]) for k in [*m.CALIBRATION_SCALES,*m.DIAGNOSTICS]}
    # Full-manuscript-size synthetic recovery: templates carry layout only,
    # training remains Currier B folds 0–2. No additional target fitting.
    large=[];nlarge=sum(len(ln['words']) for ln in lines)
    for ci,config in enumerate(configs):
        for si,(source,text) in enumerate(plain.items()):
            seed=81000+ci*100+si*10
            words,audit=m.generate(training,encoder,text[len(text)//2:],nlarge,config,seed)
            large.append(dict(config,**m.fingerprint(m.apply_template(lines,words)),source=source,seed=seed,audit=audit,corpus_sha=corpus_hash(words)))
        print('manuscript-size simulations',config,flush=True)
    (OUT/'large_simulation_features.json').write_text(json.dumps(large,indent=2))
    result['large_recovery_parameters']=recovery(large,'parameters')
    result['large_recovery_plaintext']=recovery(large,'plaintext')
    result['large_slots']=nlarge
    # Expensive family-transfer diagnostic on one independently seeded corpus
    # per best configuration. Exploratory representativeness, no intervals over
    # generator seeds are claimed. Whole manuscript layout supplies five folds.
    representative=[]
    for ci,(mechanism,config) in enumerate(best.items()):
        seed=91000+ci*100
        words,audit=m.generate(training,encoder,plain['italian'][len(plain['italian'])//2:],nlarge,config,seed)
        template=m.apply_template(lines,words)
        (OUT/f'representative_{mechanism}.txt').write_text('\n'.join(' '.join(w['word'] if w['clean'] else '?' for w in ln['words']) for ln in template)+'\n')
        rows=[dict(r,family=g.family(r['stem'])) for r in f.observations(template) if r['kind']=='ordinary']
        ff=f.assign_folds(r['family'] for r in rows)
        pred,split_audit=g.run_cross(rows,folios,ff)
        result.setdefault('representative_family_transfer',{})[mechanism]=dict(summary=g.summarize(pred),seed=seed,generation_audit=audit)
        for r in pred:r['experiment']=mechanism
        representative.extend(pred)
        print('representative family check',mechanism,flush=True)
    f.write_csv(OUT/'representative_family_predictions.csv',representative)
    result['limits']=['Specified implementations only; neither rejection nor acceptance establishes meaning.',
                      'Rejection thresholds are empirical simulation distances, not posterior probabilities.',
                      'Recovery uses few parameter levels and two plaintext works; no universal mechanism recovery claim.',
                      'Large simulations reuse observed layout counts but never its text outcomes; no layout prediction credit.',
                      'Only one best-model representative per mechanism in the costly family-transfer diagnostic.']
    (OUT/'benchmark_summary.json').write_text(json.dumps(result,indent=2))
    files=[Path(__file__).resolve(),ROOT/'code/mechanism_models.py',ROOT/'code/08_robustness_gate.py',ROOT/'MECHANISM_PROTOCOL.md',ROOT/'uv.lock',ROOT/'data/ZL3b-n.txt',ROOT/'data/latin_alfonsi.txt',ROOT/'data/italian_dante.txt',ROOT/'data/mechanisms/naibbe_tables.csv']
    (OUT/'benchmark_manifest.json').write_text(json.dumps(dict(configurations=configs,train_folios=sorted({ln['folio'] for ln in train}),test_folios=sorted({ln['folio'] for ln in test}),hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}),indent=2))
    print('Completed; recovery',result['recovery_parameters']['accuracy'],'large',result['large_recovery_parameters']['accuracy'],flush=True)


if __name__=='__main__':main()
