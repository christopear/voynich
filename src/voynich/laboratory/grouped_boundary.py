"""Calibration and immediate Voynich trial for bounded grouped prefix codes."""
import argparse
from collections import defaultdict, Counter
from dataclasses import asdict
from pathlib import Path
import random
import string
import textwrap

from voynich.ciphers.units import UnitCipher
from voynich.ciphers.models import CipherKey
from voynich.decipher_search.core import LanguageModel, normalize, digest
from voynich.evaluation.scorers import recovery_metrics
from voynich.evaluation.capacity import block_entropy
from voynich.experiments.e06_boundary_frontier import load_lines
from voynich.experiments.runner import ExperimentRunner
from voynich.laboratory.manifest import DatasetRef, ExperimentSpec, environment, fingerprint, file_hash
from voynich.laboratory.medical_recovery import sources
from voynich.laboratory.voynich_pilot import represent, clean_page
from voynich.paths import ROOT
from voynich.search.codebooks import CodebookSearch
from voynich.search.grouped import GroupedProblem, GroupedEvaluator, screen_policies, frozen_decode, parse_span
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import write_json, read_json
from voynich.storage.database import make_engine
from voynich.storage.registry import Registry


def manuscript_pages():
    pages={p:[] for p in ('f26r','f31r','f39v')}
    for ln in load_lines(ROOT/'data/ZL3b-n.txt'):
        if ln['page'] not in pages:continue
        assert ln['meta'].get('L')=='B'
        words=[represent([w['word']],'compounds')[0] if w['clean'] else None for w in ln['words']]
        pages[ln['page']].append({'locus':ln['locus'],'words':words,'gaps':ln['gaps'],
                                'first':ln['paragraph_start'],'last':ln['paragraph_end']})
    return pages


def spans_from_rows(rows):
    spans=[]
    for row in rows:
        run=[]
        for i,word in enumerate(row['words']):
            if word is None or (i and row['gaps'][i-1]=='drawing'):
                if run:spans.append(' '.join(run));run=[]
            if word is not None:run.append(word)
        if run:spans.append(' '.join(run))
    return tuple(spans)


def control_rows(rows,kind,seed):
    result=[{**r,'words':list(r['words'])} for r in rows]
    if kind=='original':return result
    rng=random.Random(seed)
    slots=[(j,i) for j,r in enumerate(rows) for i,w in enumerate(r['words']) if w is not None]
    if kind=='symbol-shuffled':
        letters=[c for j,i in slots for c in rows[j]['words'][i]];rng.shuffle(letters)
        for j,i in slots:result[j]['words'][i]=''.join(letters.pop() for _ in rows[j]['words'][i])
    else:
        groups=defaultdict(list)
        for j,i in slots:
            r=rows[j]
            role=(r['first'],r['last'],i==0,i==len(r['words'])-1) if kind.startswith('layout-') else ()
            groups[role].append((j,i))
        for group in groups.values():
            words=[rows[j]['words'][i] for j,i in group];rng.shuffle(words)
            for (j,i),word in zip(group,words):result[j]['words'][i]=word
    return result


def fixture(plain,spacing,seed):
    """Independent prefix-free encoder; no search implementation or true-key ranking."""
    method=UnitCipher('groups',homophones=2,lengths='variable',spacing=spacing,alphabet=string.ascii_uppercase[:16])
    rng=random.Random(seed+500);alphabet=list(method.alphabet);rng.shuffle(alphabet)
    prefixes=alphabet[:3]
    singles=alphabet[3:];pairs=[a+b for a in prefixes for b in alphabet];rng.shuffle(pairs)
    codes=singles+pairs[:len(method.units)*2-len(singles)];rng.shuffle(codes)
    key=CipherKey(method.method_id,tuple(zip(codes,[u for u in method.units for _ in range(2)])))
    method.validate_key(key)
    truth=tuple(textwrap.wrap(plain,50,break_long_words=False,break_on_hyphens=False))
    cipher=[]
    for i,line in enumerate(truth):
        encrypted,_=method.encrypt_text(line,key,seed=seed+1000+i)
        if spacing=='encoded':encrypted=' '.join(encrypted[j:j+5] for j in range(0,len(encrypted),5))
        cipher.append(encrypted)
    table=key.as_mapping()
    recovered=tuple(''.join(' ' if c==' ' else table[c] for c in parse_span(s,prefixes,spacing)) for s in cipher)
    if recovered!=truth:raise AssertionError('fixture round trip failed')
    return tuple(cipher),truth,table,tuple(sorted(prefixes))


def space_boundary_f1(predicted,truth):
    def boundaries(s):
        n=0;out=set()
        for c in s:
            if c==' ':out.add(n)
            else:n+=1
        return out
    p,t=boundaries(predicted),boundaries(truth)
    return 2*len(p&t)/(len(p)+len(t)) if p or t else 1.


def run(output):
    corp=sources()
    ipath=ROOT/'data/italian_dante.txt'
    corp['dante']={'text':normalize(ipath.read_text()),'path':ipath,
                   'metadata':{'work':'Dante project reference','genre':'poetry'}}
    starts={k:int(.3*len(v['text'])) for k,v in corp.items()}
    train={k:v['text'][starts[k]:starts[k]+min(12000,int(.2*len(v['text'])))] for k,v in corp.items()}
    lms={k:LanguageModel(t,4) for k,t in train.items()}
    pages=manuscript_pages();cases=[]
    def ref(name,role,start,stop,prepared,language='latin'):
        s=corp[name]
        return DatasetRef(name,language,file_hash(s['path']),digest(prepared),role,start,stop,
                          'ascii-normalized-prefix-study-v1',s['metadata']['work'])
    for language,target,trainer in (('latin','pliny','celsus'),('italian','dante','dante')):
        start=int(.7*len(corp[target]['text']));plain=corp[target]['text'][start:start+350].strip()
        for spacing in ('preserve','encoded'):
            for seed in (7,19):
                spans,truth,table,prefixes=fixture(plain,spacing,seed)
                cases.append(dict(id=f'{language}-{spacing}-{seed}',kind='synthetic',control='original',
                    language=language,spacing=spacing,seed=seed,spans=spans,trainer=trainer,truth=truth,
                    oracle_table=table,oracle_prefixes=prefixes,refs=(
                        ref(trainer,'training',starts[trainer],starts[trainer]+len(train[trainer]),train[trainer],language),
                        ref(target,'development',start,start+350,'\n'.join(spans),language))))
    source=ROOT/'data/ZL3b-n.txt'
    rawpages={p:clean_page(source,p) for p in pages}
    controls=('original','word-shuffled','symbol-shuffled','layout-1','layout-2')
    for spacing in ('preserve','encoded'):
        for control in controls:
            rows=control_rows(pages['f26r'],control,1000+(int(control[-1]) if control.startswith('layout-') else 0))
            spans=spans_from_rows(rows)
            for seed in (7,19):
                refs=[ref('celsus','training',starts['celsus'],starts['celsus']+len(train['celsus']),train['celsus']),
                      ref('pliny','evaluation',starts['pliny'],starts['pliny']+len(train['pliny']),train['pliny'])]
                for p,role in (('f26r','development'),('f31r','evaluation'),('f39v','evaluation')):
                    refs.append(DatasetRef('ZL3b','unknown',file_hash(source),digest('\n'.join(spans if p=='f26r' else spans_from_rows(pages[p]))),
                        role,*rawpages[p]['raw_line_span'],'compound-EVA-gap-preserving-v1','Voynich '+p))
                cases.append(dict(id=f'voynich-{spacing}-{control}-{seed}',kind='voynich',control=control,
                                  language='latin',spacing=spacing,seed=seed,spans=spans,trainer='celsus',refs=tuple(refs)))
    plan={'schema':1,'case_ids':[c['id'] for c in cases],'policy_limit':4,'budget_per_policy':4096,'width':8,
          'maximum_prefix_count':3,'maximum_homophones':2,'expansion':[1.35,2.0],
          'protocol_hash':file_hash(ROOT/'docs/protocols/GROUPED_BOUNDARY_2026-10-09.md'),
          'selection':'training only; no truth/Pliny criterion selects a key',
          'source_hashes':{k:file_hash(s['path']) for k,s in corp.items()},'transcription_hash':file_hash(source),
          'limits':'Candidate-family pilot; failed calibration cannot reject manuscript family; different structural survivors imply different total budgets.'}
    output.mkdir(parents=True,exist_ok=False);env=environment(ROOT)
    write_json(output/'plan.json',plan);write_json(output/'environment.json',env);write_json(output/'pages.json',pages)
    engine=make_engine();registry=Registry(engine);result_rows=[];stages=[];specs=[]
    try:
        for case in cases:
            print('CASE',case['id'],flush=True)
            screening=screen_policies(case['spans'],train[case['trainer']],case['spacing'])
            row={k:case[k] for k in ('id','kind','control','language','spacing','seed','spans')}
            row['screening']=screening;row['runs']=[]
            glyphs=''.join(case['spans']).replace(' ','')
            words=[w for span in case['spans'] for w in span.split()]
            wc=Counter(words)
            row['input_profile']={'glyphs':len(glyphs),'alphabet':len(set(glyphs)),
                'block_entropies':{str(n):block_entropy(glyphs,n) for n in (1,2,3,4)},
                'visible_word_types':len(wc),'visible_word_tokens':len(words),
                'top10_share':sum(n for _,n in wc.most_common(10))/max(1,len(words)),
                'scope':'Short-sample fingerprints, not calibrated compatibility; synthetic layout/topic mismatch remains.'}
            selected=[]
            for policy in screening['selected']:
                p=GroupedProblem(case['spans'],train[case['trainer']],tuple(policy['prefixes']),case['spacing'])
                strategy=CodebookSearch(p,algorithm='beam',seed=case['seed'],width=8,budget=4096)
                evaluator=GroupedEvaluator(p)
                binding=fingerprint({'strategy':strategy.identity(),'evaluator':evaluator.identity(),'batch_size':8})
                spec=ExperimentSpec.create(family='grouped-prefix',method_version='grouped-prefix-v1',datasets=case['refs'],
                    configuration={'case_id':case['id'],'policy':policy,'plan_hash':fingerprint(plan),'execution_binding':binding},
                    environment=env,max_evaluations=4096,seed=case['seed'],retention={'top_k':3,'reservoir':3})
                result=ExperimentRunner(registry,output/'runs').run(spec,strategy,evaluator,batch_size=8)
                specs.append(spec.data)
                best=result['top'][0]
                # Replay the selected output immediately, before exporting any conclusion.
                replay=evaluator(Candidate.create(**best['candidate']))
                if replay.loss!=best['loss'] or replay.payload!=best['payload']:raise AssertionError('replay mismatch')
                selected.append({'policy':policy,'run_id':result['run_id'],**best})
                row['runs'].append(result['run_id'])
                stages.append({'run_id':result['run_id'],'case_id':case['id'],'evaluations':result['evaluations'],
                               'failures':result['failures'],'top':result['top'],'spec_id':spec.id})
            row['selected']=min(selected,key=lambda x:(x['loss'],x['run_id'])) if selected else None
            if row['selected']:
                best=row['selected'];payload=best['payload'];chars=sum(map(len,payload['plaintext_spans']))
                row['language_metrics']={n:sum(lm.nll(s) for s in payload['plaintext_spans'])/max(1,chars)
                                         for n,lm in lms.items() if n in (case['trainer'],'pliny')}
                row['transfer']={}
                if case['kind']=='voynich':
                    for page in ('f31r','f39v'):
                        row['transfer'][page]=frozen_decode(spans_from_rows(pages[page]),best['policy']['prefixes'],
                                                          case['spacing'],payload['table'],lms['pliny'])
            if case['kind']=='synthetic':
                truth='\n'.join(case['truth'])
                row['calibration']={'truth_spans':case['truth'],'oracle_table':case['oracle_table'],
                    'oracle_prefixes':case['oracle_prefixes'],'known_key_roundtrip':True,
                    'oracle_policy_shortlisted':list(case['oracle_prefixes']) in [p['prefixes'] for p in screening['selected']],
                    'recovery':recovery_metrics(row['selected']['payload']['plaintext'].replace('\n',''),truth.replace('\n','')) if row['selected'] else None,
                    'space_boundary_f1':space_boundary_f1(row['selected']['payload']['plaintext'].replace('\n',''),truth.replace('\n','')) if row['selected'] else None}
                active={c for s in case['spans'] for c in parse_span(s,case['oracle_prefixes'],case['spacing']) if c!=' '}
                op=GroupedProblem(case['spans'],train[case['trainer']],case['oracle_prefixes'],case['spacing'])
                oracle=Candidate.create('explicit-codebook-v1',key={op.ids[c]:case['oracle_table'][c] for c in active},long_prefixes=[])
                oe=GroupedEvaluator(op)(oracle)
                row['calibration']['oracle_loss']=oe.loss
                if oe.payload['plaintext_spans']!=list(case['truth']):raise AssertionError('oracle evaluator mismatch')
            result_rows.append(row);write_json(output/'rows'/f'{len(result_rows):03}.json',row)
            print('RESULT',case['id'],screening['counts'],'loss',row['selected']['loss'] if row['selected'] else None,
                  'recovery',row.get('calibration',{}).get('recovery'),flush=True)
        evidence={'plan':plan,'rows':result_rows,'stages':stages,'registered_evaluations':sum(s['evaluations'] for s in stages)}
        write_json(output/'evidence.json',evidence);write_json(output/'specifications.json',specs)
        return evidence
    finally:engine.dispose()


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    run(ap.parse_args().output)
