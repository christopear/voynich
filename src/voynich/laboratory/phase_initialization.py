"""Equal-budget calibration followed immediately by controlled Voynich trials."""
import argparse
from dataclasses import replace
from pathlib import Path
import textwrap

from voynich.decipher_search.core import LanguageModel, digest
from voynich.evaluation.scorers import recovery_metrics
from voynich.experiments.runner import ExperimentRunner
from voynich.laboratory.manifest import DatasetRef, ExperimentSpec, environment, file_hash, fingerprint
from voynich.laboratory.medical_recovery import sources
from voynich.laboratory.rotation_pilot import controlled, page_lines, synthetic, word_hits
from voynich.laboratory.voynich_pilot import language_metrics
from voynich.paths import ROOT
from voynich.search.line_tables import (LineTableEvaluator,LineTableSearch,SeparateLineEvaluator,
    InitializedLineTableSearch,combine_phase_winners,transfer)
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import read_json,write_json
from voynich.storage.database import make_engine
from voynich.storage.registry import Registry


def cases(previous,corpora):
    evidence=read_json(previous/'evidence.json')
    specs=read_json(previous/'specifications.json')['specifications']
    refs={s['run_id']:tuple(DatasetRef(**d) for d in s['manifest_without_environment']['datasets']) for s in specs}
    result=[]
    for row in evidence['runs']:
        if row['period']!=2:continue
        held={}
        if row['case']=='voynich':
            control=row['control'];cs=1000+(int(control[-1]) if control.startswith('line-shuffled-') else 0)
            held={p:controlled(page_lines(evidence['pages'][p]),control,cs+1000) for p in evidence['plan']['transfer']}
        result.append({'id':f"{row['case']}-{row['seed']}-{row['control']}",'kind':row['case'],
            'seed':row['seed'],'control':row['control'],'lines':tuple(row['lines']),'held':held,
            'refs':refs[row['run_id']],'previous_run_id':row['run_id'],
            'truth':row.get('calibration',{}).get('truth'),
            'oracle':row.get('calibration',{}).get('oracle_candidate')})
    template=next(c for c in result if c['kind']=='synthetic')
    for seed,fraction in ((31,.70),(43,.75)):
        source=corpora['pliny'];start=int(fraction*len(source['text']))
        plain=tuple(textwrap.wrap(source['text'][start:start+600],50,break_long_words=False,break_on_hyphens=False))
        cipher,oracle=synthetic(plain,2,seed+500)
        updated=tuple(replace(d,start=start,stop=start+600,prepared_hash=digest(' '.join(cipher)))
                      if d.role=='development' else d for d in template['refs'])
        result.append({'id':f'synthetic-{seed}-original','kind':'synthetic','seed':seed,'control':'original',
            'lines':cipher,'held':{},'refs':updated,'previous_run_id':None,
            'truth':' '.join(plain),'oracle':oracle.data})
    return sorted(result,key=lambda c:(c['kind']!='synthetic',c['seed'],c['control']))


def run(output,previous):
    corpora=sources();case_list=cases(previous,corpora)
    training={n:s['text'][int(.3*len(s['text'])):int(.3*len(s['text']))+60000] for n,s in corpora.items()}
    for case in case_list:
        for ref in case['refs']:
            if ref.source_id in corpora and file_hash(corpora[ref.source_id]['path'])!=ref.raw_hash:
                raise ValueError('source differs from previous registered experiment')
            if ref.role=='training' and ref.prepared_hash!=digest(training['celsus']):
                raise ValueError('training differs from previous registered experiment')
    if len(case_list)!=14:raise ValueError('expected four synthetic and ten manuscript/control cases')
    lms={n:LanguageModel(text,4) for n,text in training.items()}
    plan={'schema':1,'variants':['cold','separate-then-joint'],'period':2,'population':8,
          'cold_budget':8192,'phase_budgets':[2048,2048],'joint_budget':4096,
          'case_ids':[c['id'] for c in case_list],'previous_evidence_hash':file_hash(previous/'evidence.json'),
          'registered_runs':56,'registered_evaluations':229376,
          'scope':'Optimization comparison followed by Voynich immediately; not evidence of decipherment by itself.'}
    output.mkdir(parents=True,exist_ok=False);write_json(output/'plan.json',plan)
    env=environment(ROOT);write_json(output/'environment.json',env)
    engine=make_engine();registry=Registry(engine);rows=[];stage_rows=[]
    def execute(case,variant,stage,strategy,evaluator,refs):
        binding=fingerprint({'strategy':strategy.identity(),'evaluator':evaluator.identity(),'batch_size':8})
        config={'case_id':case['id'],'case':case['kind'],'control':case['control'],'variant':variant,
                'stage':stage,'execution_binding':binding,'plan_hash':fingerprint(plan)}
        spec=ExperimentSpec.create(family='line-table-initialization',method_version='line-table-v1',
            datasets=refs,configuration=config,environment=env,max_evaluations=strategy.budget,seed=case['seed'],
            retention={'top_k':3,'reservoir':3})
        print(case['id'],variant,stage,flush=True)
        result=ExperimentRunner(registry,output/'runs').run(spec,strategy,evaluator,batch_size=8)
        stage_rows.append({**config,'run_id':result['run_id'],'evaluations':result['evaluations'],
                           'failures':result['failures'],'selected':result['top'][0]})
        return result
    try:
        for case in case_list:
            selected={}
            for variant in plan['variants']:
                stage_ids=[]
                if variant=='cold':
                    strategy=LineTableSearch(case['lines'],training['celsus'],2,seed=case['seed'],budget=8192)
                else:
                    phase_results=[]
                    for phase in (0,1):
                        lines=case['lines'][phase::2]
                        refs=tuple(replace(d,prepared_hash=digest('\n'.join(lines)),
                                          normalization=d.normalization+f'/assigned-phase-{phase}-of-2')
                                   if d.role=='development' else d for d in case['refs'])
                        search=LineTableSearch(lines,training['celsus'],1,seed=case['seed'],budget=2048)
                        evaluator=SeparateLineEvaluator(lines,training['celsus'])
                        result=execute(case,variant,f'phase-{phase}',search,evaluator,refs)
                        phase_results.append(result['top']);stage_ids.append(result['run_id'])
                    starts=combine_phase_winners(phase_results)
                    strategy=InitializedLineTableSearch(case['lines'],training['celsus'],2,starts,
                        seed=case['seed'],budget=4096)
                evaluator=LineTableEvaluator(case['lines'],training['celsus'],2)
                result=execute(case,variant,'joint',strategy,evaluator,case['refs']);stage_ids.append(result['run_id'])
                best=result['top'][0];candidate=Candidate.create(**best['candidate']);plain=best['payload']['plaintext']
                row={'case_id':case['id'],'case':case['kind'],'control':case['control'],'seed':case['seed'],
                     'variant':variant,'run_ids':stage_ids,'search_budget':8192,'selected_loss':best['loss'],
                     'score':best['score'],'candidate':candidate.data,'plaintext':plain,'lines':case['lines'],
                     'metrics':{n:language_metrics(plain,lm) for n,lm in lms.items()},
                     'word_hits':{n:word_hits(plain,lm) for n,lm in lms.items()},'transfer':{},
                     'previous_run_id':case['previous_run_id']}
                for p,lines in case['held'].items():
                    t=transfer(lines,2,candidate)
                    t['metrics']={n:language_metrics(t['plaintext'],lm) for n,lm in lms.items()}
                    t['word_hits']={n:word_hits(t['plaintext'],lm) for n,lm in lms.items()}
                    row['transfer'][p]=t
                selected[variant]=row
            # Neither truth nor independent-model score selects initialization or final candidates.
            if case['truth'] is not None:
                oracle=LineTableEvaluator(case['lines'],training['celsus'],2)(Candidate.create(**case['oracle']))
                if oracle.payload['plaintext']!=case['truth']:raise AssertionError('oracle mismatch')
                for row in selected.values():
                    row['calibration']={'truth':case['truth'],'oracle_loss':oracle.loss,
                                        'recovery':recovery_metrics(row['plaintext'],case['truth'])}
            for row in selected.values():
                rows.append(row);write_json(output/'rows'/f'{len(rows):03}.json',row)
                print('RESULT',case['id'],row['variant'],round(row['selected_loss'],3),
                      row.get('calibration',{}).get('recovery',{}),flush=True)
        evidence={'plan':plan,'rows':rows,'stages':stage_rows,
                  'registered_evaluations':sum(s['evaluations'] for s in stage_rows)}
        write_json(output/'evidence.json',evidence);return evidence
    finally:engine.dispose()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--previous',type=Path,default=ROOT/'results/line_rotation_2026-10-09')
    args=parser.parse_args();run(args.output,args.previous)
