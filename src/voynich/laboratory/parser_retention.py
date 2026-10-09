"""All-survivor synthetic calibration; reuses exactly compatible prior searches."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from voynich.decipher_search.core import normalize, digest
from voynich.evaluation.scorers import recovery_metrics
from voynich.experiments.runner import ExperimentRunner
from voynich.laboratory.manifest import DatasetRef, ExperimentSpec, environment, file_hash, fingerprint
from voynich.paths import ROOT
from voynich.search.codebooks import CodebookSearch
from voynich.search.grouped import GroupedProblem, GroupedEvaluator, screen_policies
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import read_json, write_json
from voynich.storage.database import make_engine
from voynich.storage.registry import Registry


def retained_policies(spans, training, spacing):
    # The historical function remains unchanged for historical reproducibility.
    # Its ranking does NOT discard any candidate in this follow-up.
    return sorted(screen_policies(spans,training,spacing)['survivors'],key=lambda p:p['prefixes'])


def run_case(task):
    row,old_stages,old_specs,env,plan,output=task
    output=Path(output);case=row['id'];seed=row['seed']
    old_by_id={fingerprint(s):s for s in old_specs}
    template=old_by_id[old_stages[0]['spec_id']]
    refs=tuple(DatasetRef(**r) for r in template['datasets'])
    tr=next(r for r in refs if r.role=='training')
    path=ROOT/('data/italian_dante.txt' if tr.source_id=='dante' else f'data/laboratory_sources/{tr.source_id}_medical.txt')
    if file_hash(path)!=tr.raw_hash:raise ValueError('changed training corpus')
    training=normalize(path.read_text())[tr.start:tr.stop]
    if digest(training)!=tr.prepared_hash:raise ValueError('training slice mismatch')
    policies=retained_policies(tuple(row['spans']),training,row['spacing'])
    if policies!=sorted(row['screening']['survivors'],key=lambda p:p['prefixes']):raise ValueError('screen changed')
    previous={tuple(old_by_id[s['spec_id']]['configuration']['policy']['prefixes']):s for s in old_stages}
    engine=make_engine();registry=Registry(engine);stages=[];specs=[]
    try:
        for index,policy in enumerate(policies):
            p=GroupedProblem(tuple(row['spans']),training,tuple(policy['prefixes']),row['spacing'])
            evaluator=GroupedEvaluator(p);strategy=CodebookSearch(p,algorithm='beam',seed=seed,width=8,budget=4096)
            binding=fingerprint({'strategy':strategy.identity(),'evaluator':evaluator.identity(),'batch_size':8})
            old=previous.get(tuple(policy['prefixes']))
            if old:
                if old_by_id[old['spec_id']]['configuration']['execution_binding']!=binding:raise ValueError('incompatible old execution')
                stored=registry.get(old['run_id'])
                if stored['sequence']!=4096 or stored['checkpoint']['top']!=old['top']:raise ValueError('old registry mismatch')
                stage={**old,'reused':True,'policy':policy}
            else:
                spec=ExperimentSpec.create(family='grouped-parser-retention',method_version='grouped-prefix-v1',datasets=refs,
                    configuration={'case_id':case,'policy':policy,'plan_hash':fingerprint(plan),'execution_binding':binding},
                    environment=env,max_evaluations=4096,seed=seed,retention={'top_k':3,'reservoir':3})
                result=ExperimentRunner(registry,output/'runs').run(spec,strategy,evaluator,batch_size=8)
                specs.append(spec.data)
                stage={'case_id':case,'run_id':result['run_id'],'spec_id':spec.id,'reused':False,'policy':policy,
                       'evaluations':result['evaluations'],'failures':result['failures'],'top':result['top']}
            for best in stage['top']:
                replay=evaluator(Candidate.create(**best['candidate']))
                if replay.loss!=best['loss'] or replay.payload!=best['payload']:raise AssertionError('replay mismatch')
            stages.append(stage)
            write_json(output/'policies'/f'{case}-{index:03}.json',stage)
            print(case,index+1,'/',len(policies),'reused' if old else 'new',flush=True)
        chosen=min(stages,key=lambda s:(s['top'][0]['loss'],s['policy']['prefixes'],s['top'][0]['candidate_id']))
        # Private calibration information first affects work here, after selection.
        truth=''.join(row['calibration']['truth_spans'])
        true_prefixes=row['calibration']['oracle_prefixes']
        true_stage=next(s for s in stages if s['policy']['prefixes']==true_prefixes)
        score=lambda s:recovery_metrics(s['top'][0]['payload']['plaintext'].replace('\n',''),truth)
        result={'case_id':case,'spacing':row['spacing'],'language':row['language'],'seed':seed,
            'policies':len(stages),'new_runs':sum(not s['reused'] for s in stages),'selected':chosen,
            'selected_recovery':score(chosen),'true_policy_branch':true_stage,'true_policy_recovery':score(true_stage),
            'selected_true_policy':chosen['policy']['prefixes']==true_prefixes,
            'oracle_loss':row['calibration']['oracle_loss'],'previous_recovery':row['calibration']['recovery'],
            'true_parser_retained':True,'gate_pass':score(chosen)['nonspace_edit_accuracy']>=.9,
            'true_policy_gate_pass':score(true_stage)['nonspace_edit_accuracy']>=.9}
        write_json(output/'cases'/f'{case}.json',result)
        return result,stages,specs
    finally:engine.dispose()


def run(output,previous,workers=4):
    evidence=read_json(previous/'evidence.json');specs=read_json(previous/'specifications.json')
    cases=[r for r in evidence['rows'] if r['kind']=='synthetic']
    plan={'schema':1,'case_ids':[r['id'] for r in cases],'per_policy_budget':4096,'beam_width':8,
          'parser_retention':'all structural survivors','expected_policies':177,'expected_reused':32,'case_workers':workers,
          'prior_evidence_sha256':file_hash(previous/'evidence.json'),
          'protocol_sha256':file_hash(ROOT/'docs/protocols/PARSER_RETENTION_2026-10-09.md')}
    if sum(r['screening']['counts']['surviving'] for r in cases)!=177:raise ValueError('unexpected case inventory')
    output.mkdir(parents=True,exist_ok=False);env=environment(ROOT)
    write_json(output/'plan.json',plan);write_json(output/'environment.json',env)
    tasks=[(r,[s for s in evidence['stages'] if s['case_id']==r['id']],specs,env,plan,str(output)) for r in cases]
    results=[];stages=[];new_specs=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for f in as_completed([pool.submit(run_case,t) for t in tasks]):
            result,ss,spec=f.result();results.append(result);stages+=ss;new_specs+=spec
            print('CASE COMPLETE',result['case_id'],result['selected_recovery'],flush=True)
    stages.sort(key=lambda s:(s['case_id'],s['policy']['prefixes']));results.sort(key=lambda r:r['case_id'])
    out={'plan':plan,'cases':results,'stages':stages,'new_evaluations':sum(s['evaluations'] for s in stages if not s['reused']),
         'represented_evaluations':sum(s['evaluations'] for s in stages),'failures':sum(s['failures'] for s in stages),
         'replayed_candidates':sum(len(s['top']) for s in stages)}
    write_json(output/'evidence.json',out);write_json(output/'new_specifications.json',new_specs)
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--previous',type=Path,default=ROOT/'results/grouped_boundary_2026-10-09');ap.add_argument('--workers',type=int,default=4)
    args=ap.parse_args();run(args.output,args.previous,args.workers)
