"""Independent-author medical calibration with matched candidate budgets."""
import argparse
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
import random

from voynich.ciphers.units import UnitCipher
from voynich.decipher_search.core import normalize, digest
from voynich.evaluation.scorers import recovery_metrics, model
from voynich.experiments.runner import ExperimentRunner
from voynich.laboratory.fixtures import PublicInput
from voynich.laboratory.manifest import DatasetRef,ExperimentSpec,environment,file_hash,fingerprint,stream_seed
from voynich.laboratory.oracle_audit import classify_gap
from voynich.paths import ROOT
from voynich.search.codebooks import CodebookProblem,CodebookEvaluator,CodebookSearch,partial_transfer,tokenize
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import read_json,write_json
from voynich.storage.database import make_engine
from voynich.storage.registry import Registry


def sources(root=ROOT):
    out={}
    for name in ('celsus','pliny'):
        path=root/'data/laboratory_sources'/f'{name}_medical.txt'
        meta=read_json(Path(str(path)+'.source.json'))
        if file_hash(path)!=meta['text_sha256']:raise ValueError('medical source hash mismatch')
        out[name]={'text':normalize(path.read_text()),'metadata':meta,'path':path}
    return out


def shuffled_codes(cipher,alignment,seed):
    """Matched control: shuffle whole codes among equal-length slots.

    Generator-side alignment is allowed here, never supplied to the optimizer.
    Preserves code counts, character counts and word-space positions.
    """
    rng=random.Random(seed);tokens=[cipher[a:b] for _,_,a,b in alignment]
    groups={n:[c for c in tokens if c!=' ' and len(c)==n] for n in (1,2)}
    for values in groups.values():rng.shuffle(values)
    return ''.join(' ' if c==' ' else groups[len(c)].pop() for c in tokens)


def method_for(family,training):
    pairs=tuple(p for p,_ in Counter(training[i:i+2] for i in range(len(training)-1)
                                   if ' ' not in training[i:i+2]).most_common(8))
    if family=='glyph':return UnitCipher(),1,1
    if family=='homophonic':return UnitCipher(homophones=2),1,2
    if family=='groups-fixed':return UnitCipher('groups',extra_units=pairs),2,1
    if family=='groups-variable':return UnitCipher('groups',lengths='variable',extra_units=pairs),None,2
    raise ValueError('unknown family')


def run(plan,output):
    corpora=sources();env=environment(ROOT)
    for name,source in corpora.items():
        if file_hash(source['path'])!=plan['source_hashes'][name]:raise ValueError('plan source changed')
    output.mkdir(parents=True,exist_ok=False);write_json(output/'plan.json',plan)
    write_json(output/'environment.json',env)
    engine=make_engine();registry=Registry(engine);rows=[]
    narrative=normalize((ROOT/'data/latin_alfonsi.txt').read_text())[:plan['training_length']]
    try:
        for target_id in plan['targets']:
            target=corpora[target_id];train_id='pliny' if target_id=='celsus' else 'celsus';train=corpora[train_id]
            ts=int(plan['training_start_fraction']*len(train['text']))
            training=train['text'][ts:ts+plan['training_length']]
            for index,seed in enumerate(plan['seeds']):
                start=int(plan['development_fraction']*len(target['text']))+index*plan['passage_stride']
                fs=int(plan['frozen_fraction']*len(target['text']))+index*plan['passage_stride']
                plain=target['text'][start:start+plan['length']]
                frozen=target['text'][fs:fs+plan['length']]
                start+=len(plain)-len(plain.lstrip());fs+=len(frozen)-len(frozen.lstrip())
                plain=plain.strip();frozen=frozen.strip()
                refs=[]
                for source_id,source,role,a,text in ((train_id,train,'training',ts,training),
                        (target_id,target,'development',start,plain),(target_id,target,'evaluation',fs,frozen)):
                    m=source['metadata'];refs.append(DatasetRef(source_id,'latin',file_hash(source['path']),digest(text),
                        role,a,a+len(text),'ascii-fold-ae-oe-preserve-ij-uv-v1',m['work'],m['url'],m['genre']))
                for family in plan['families']:
                    method,width,capacity=method_for(family,training)
                    key=method.generate_key(seed=seed)
                    cipher,alignment=method.encrypt_text(plain,key,seed=seed+1)
                    frozen_cipher,frozen_alignment=method.encrypt_text(frozen,key,seed=seed+2)
                    case=f'{target_id}-{family}-{seed}'
                    public=PublicInput(cipher,method.method_id,'preserve')
                    problem=CodebookProblem(public,training,method.units,width,capacity)
                    selected={}
                    for algorithm in plan['algorithms']:
                        for control in plan['controls']:
                            text=cipher if control=='positive' else shuffled_codes(cipher,alignment,stream_seed(seed,case,'negative'))
                            p=replace(problem,public=replace(public,ciphertext=text))
                            strategy=CodebookSearch(p,algorithm=algorithm,seed=seed,width=plan['population'],budget=plan['budget'])
                            evaluator=CodebookEvaluator(p)
                            binding=fingerprint({'strategy':strategy.identity(),'evaluator':evaluator.identity(),'batch_size':plan['population']})
                            spec=ExperimentSpec.create(family=family,method_version=method.method_id,datasets=tuple(refs),
                                configuration={'execution_binding':binding,'case':case,'plan_hash':fingerprint(plan),
                                    'algorithm':algorithm,'control':control,'fixture_seed':seed,
                                    'known_assumptions':{'spacing':'preserved word spaces','emissions':method.units,
                                        'width':width,'maximum_codes_per_unit':capacity},'cross_author':True},
                                environment=env,max_evaluations=plan['budget'],seed=seed,
                                retention={'top_k':3,'reservoir':3})
                            print(case,algorithm,control,flush=True)
                            result=ExperimentRunner(registry,output/'runs').run(spec,strategy,evaluator,batch_size=plan['population'])
                            selected[(algorithm,control)]=result
                    # Oracle diagnostics are evaluated only after all selections for this case.
                    active={cipher[a:b] for _,_,a,b in alignment}-{' '}
                    true=key.as_mapping()
                    oracle=Candidate.create('explicit-codebook-v1',key={c:true[c] for c in active},
                        long_prefixes=sorted({c[0] for c in true if len(c)==2}))
                    oracle_eval=CodebookEvaluator(problem)(oracle)
                    if oracle_eval.payload.get('plaintext')!=plain:
                        raise AssertionError('declared family fails oracle representation check')
                    write_json(output/'private-fixtures'/f'{case}.json',{'plaintext':plain,'ciphertext':cipher,
                        'key':true,'alignment':alignment,'frozen_plaintext':frozen,'frozen_ciphertext':frozen_cipher,
                        'frozen_alignment':frozen_alignment})
                    for algorithm in plan['algorithms']:
                        positive=selected[(algorithm,'positive')];negative=selected[(algorithm,'token-shuffled')]
                        best=positive['top'][0] if positive['top'] else None
                        if best:
                            candidate=Candidate.create('explicit-codebook-v1',key=best['candidate']['key'],long_prefixes=best['candidate'].get('long_prefixes',[]))
                            metrics=recovery_metrics(best['payload']['plaintext'],plain)
                            transfer=partial_transfer(replace(problem,public=replace(public,ciphertext=frozen_cipher,role='evaluation')),candidate)
                            transfer['metrics']=recovery_metrics(transfer['plaintext'],frozen)
                            negative_loss=negative['top'][0]['loss'] if negative['top'] else None
                            beats=negative_loss is not None and best['loss']<negative_loss
                            gate=metrics['nonspace_edit_accuracy']>=plan['criteria']['development_nonspace'] and transfer['valid_segmentation'] and transfer['code_token_coverage']==1 and transfer['metrics']['nonspace_edit_accuracy']>=plan['criteria']['frozen_nonspace'] and beats
                            pred_boundaries={b for c,a,b in tokenize(cipher,width,candidate.data.get('long_prefixes',())) if c!=' '}
                            true_boundaries={b for _,_,a,b in alignment if cipher[a:b]!=' '}
                            boundary_f1=2*len(pred_boundaries&true_boundaries)/max(1,len(pred_boundaries)+len(true_boundaries))
                        else:
                            metrics=recovery_metrics('',plain);transfer=None;beats=gate=False;boundary_f1=0;negative_loss=None
                        row={'case':case,'target':target_id,'training_author':train_id,'seed':seed,'family':family,'algorithm':algorithm,
                            'run_ids':{c:selected[(algorithm,c)]['run_id'] for c in plan['controls']},
                            'metrics':metrics,'selected_loss':best['loss'] if best else None,'negative_loss':negative_loss,
                            'oracle_loss':oracle_eval.loss,'oracle_score':asdict(oracle_eval.score),
                            'diagnosis':classify_gap(metrics['nonspace_edit_accuracy'],oracle_eval.loss,best['loss'] if best else None),
                            'boundary_f1':boundary_f1,'frozen':transfer,'beats_shuffled':beats,'screening_gate':gate,
                            'truth_nll_medical_per_character':model(training,4).nll(plain)/len(plain),
                            'truth_nll_narrative_per_character':model(narrative,4).nll(plain)/len(plain),
                            'budget':plan['budget'],'evaluations':positive['evaluations']+negative['evaluations'],
                            'invalid_candidates':{c:selected[(algorithm,c)]['strategy_diagnostics']['invalid_candidates'] for c in plan['controls']},
                            'examples':{'truth':plain,'ciphertext':cipher,'recovered':best['payload']['plaintext'] if best else '',
                                        'frozen_truth':frozen},
                            'assumptions':{'width':width,'capacity':capacity,'units':method.units},
                            'source_spans':{'training':[ts,ts+len(training)],'development':[start,start+len(plain)],'evaluation':[fs,fs+len(frozen)]}}
                        rows.append(row);write_json(output/'cases'/f'{case}-{algorithm}.json',row)
                        print('RESULT',case,algorithm,round(metrics['nonspace_edit_accuracy'],4),row['diagnosis'],gate,flush=True)
        summary={'schema':1,'status':'completed','plan':plan,'cases':rows,'sources':{n:s['metadata'] for n,s in corpora.items()},
            'total_evaluations':sum(r['evaluations'] for r in rows),'scope':'cross-author Latin medical screening; one shuffled control only; not calibrated family exclusion; seeds paired with distinct passages'}
        write_json(output/'summary.json',summary);return summary
    finally:engine.dispose()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(read_json(a.plan),a.output)
