"""Controlled one-table versus alternating-line-table Voynich experiment."""
import argparse
from pathlib import Path
import random
import string
import textwrap

from voynich.decipher_search.core import digest, LanguageModel
from voynich.evaluation.scorers import recovery_metrics
from voynich.experiments.runner import ExperimentRunner
from voynich.laboratory.manifest import DatasetRef, ExperimentSpec, environment, file_hash, fingerprint
from voynich.laboratory.medical_recovery import sources
from voynich.laboratory.voynich_pilot import clean_page, represent, language_metrics
from voynich.paths import ROOT
from voynich.search.line_tables import LineTableEvaluator, LineTableSearch, transfer, phase_text
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import read_json, write_json
from voynich.storage.database import make_engine
from voynich.storage.registry import Registry


def page_lines(page):
    """Preserve all paragraph-text line slots, including fully omitted lines."""
    return tuple(represent([w for w,locus in zip(page['words'],page['word_loci']) if locus==line],
                           'compounds')[0] for line in page['loci'])


def controlled(lines, control, seed):
    rng = random.Random(seed)
    if control == 'original':
        return tuple(lines)
    if control.startswith('line-shuffled-'):
        out=list(lines); rng.shuffle(out); return tuple(out)
    if control == 'symbol-shuffled':
        chars=list(''.join(lines).replace(' ','')); rng.shuffle(chars)
        return tuple(''.join(' ' if c==' ' else chars.pop() for c in line) for line in lines)
    raise ValueError('unsupported control')


def synthetic(lines, period, seed):
    """Independent encoder: one random bijection per line state, spaces kept."""
    rng=random.Random(seed); tables=[]
    for _ in range(period):
        codes=list(string.ascii_uppercase); rng.shuffle(codes)
        tables.append(dict(zip(string.ascii_lowercase,codes)))
    cipher=tuple(''.join(' ' if c==' ' else tables[i%period][c] for c in line) for i,line in enumerate(lines))
    decoding={chr(ord(c)+phase*65536):u for phase,table in enumerate(tables) for u,c in table.items()}
    active=set(phase_text(cipher,period))-{' '}
    return cipher, Candidate.create('line-table-v1', key={c:decoding[c] for c in active})


def word_hits(text, lm):
    words=[w for w in text.split() if len(w)>=4 and '?' not in w]
    hits=[w for w in words if w in lm.words]
    return {'eligible_tokens':len(words),'matched_tokens':len(hits),
            'fraction':len(hits)/len(words) if words else None,'distinct_hits':sorted(set(hits))}


def run(output, budget=4096):
    if budget<8: raise ValueError('budget must cover initialization')
    path=ROOT/'data/ZL3b-n.txt'
    pages={p:clean_page(path,p,include_alignment=True) for p in ('f26r','f31r','f39v')}
    if any(p['metadata'].get('L')!='B' or p['metadata'].get('I')!='H' for p in pages.values()):
        raise ValueError('requires Currier B herbal pages')
    corpora=sources(); starts={n:int(.3*len(s['text'])) for n,s in corpora.items()}
    texts={n:s['text'][starts[n]:starts[n]+60000] for n,s in corpora.items()}
    lms={n:LanguageModel(t,4) for n,t in texts.items()}; training=texts['celsus']
    plan={'schema':1,'budget':budget,'population':8,'periods':[1,2],'seeds':[7,19],
          'controls':['original','line-shuffled-1','line-shuffled-2','line-shuffled-3','symbol-shuffled'],
          'development':'f26r','transfer':['f31r','f39v'],'representation':'compound-EVA',
          'clock':'paragraph-text line index; first line phase zero; reset every page',
          'search_model':'celsus','post_selection_model':'pliny','transcription_sha256':file_hash(path),
          'registered_runs':24,'registered_evaluations':24*budget,
          'scope':'One or two injective tables, preserved spaces, no historical attestation or decipherment claim.'}
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/'plan.json',plan);write_json(output/'pages.json',pages)
    env=environment(ROOT);write_json(output/'environment.json',env)
    engine=make_engine();registry=Registry(engine);rows=[]
    train_ref=DatasetRef('celsus','latin',file_hash(corpora['celsus']['path']),digest(training),'training',
        starts['celsus'],starts['celsus']+len(training),'ascii-fold-ae-oe-preserve-ij-uv-v1',corpora['celsus']['metadata']['work'])
    pliny_ref=DatasetRef('pliny','latin',file_hash(corpora['pliny']['path']),digest(texts['pliny']),'evaluation',
        starts['pliny'],starts['pliny']+len(texts['pliny']),'ascii-fold-ae-oe-preserve-ij-uv-v1',corpora['pliny']['metadata']['work'])
    try:
        for case in ('synthetic','voynich'):
            for period in plan['periods']:
                for seed in plan['seeds']:
                    for control in (['original'] if case=='synthetic' else plan['controls']):
                        truth=None;oracle=None;refs=[train_ref,pliny_ref]
                        if case=='synthetic':
                            start=int(.65*len(corpora['pliny']['text']))
                            source_text=corpora['pliny']['text'][start:start+600]
                            plain_lines=tuple(textwrap.wrap(source_text,50,break_long_words=False,break_on_hyphens=False))
                            lines,oracle=synthetic(plain_lines,period,seed+500)
                            truth=' '.join(plain_lines)
                            held={}
                            refs.append(DatasetRef('pliny','latin',file_hash(corpora['pliny']['path']),digest(' '.join(lines)),
                                'development',start,start+len(source_text),'word-wrapped-50-and-injective-line-cipher-v1',corpora['pliny']['metadata']['work']))
                        else:
                            control_seed=1000+(int(control[-1]) if control.startswith('line-shuffled-') else 0)
                            lines=controlled(page_lines(pages['f26r']),control,control_seed)
                            held={p:controlled(page_lines(pages[p]),control,control_seed+1000) for p in plan['transfer']}
                            for p,value,role in [('f26r',lines,'development')]+[(p,v,'evaluation') for p,v in held.items()]:
                                refs.append(DatasetRef('ZL3b','unknown',file_hash(path),digest('\n'.join(value)),role,
                                    *pages[p]['raw_line_span'],'certain-words-compound-EVA-with-original-line-slots-v1','Voynich '+p))
                        evaluator=LineTableEvaluator(lines,training,period)
                        strategy=LineTableSearch(lines,training,period,seed=seed,budget=budget)
                        binding=fingerprint({'strategy':strategy.identity(),'evaluator':evaluator.identity(),'batch_size':8})
                        config={'case':case,'period':period,'control':control,'plan_hash':fingerprint(plan),
                                'execution_binding':binding}
                        spec=ExperimentSpec.create(family='line-table-rotation',method_version='line-table-v1',
                            datasets=tuple(refs),configuration=config,environment=env,max_evaluations=budget,seed=seed,
                            retention={'top_k':3,'reservoir':3})
                        print(case,'period',period,'seed',seed,control,flush=True)
                        result=ExperimentRunner(registry,output/'runs').run(spec,strategy,evaluator,batch_size=8)
                        best=result['top'][0];candidate=Candidate.create(**best['candidate'])
                        text=best['payload']['plaintext']
                        row={**config,'seed':seed,'run_id':result['run_id'],'evaluations':result['evaluations'],
                             'failures':result['failures'],'selected_loss':best['loss'],'score':best['score'],
                             'candidate':candidate.data,'plaintext':text,'lines':lines,
                             'metrics':{n:language_metrics(text,lm) for n,lm in lms.items()},
                             'word_hits':{n:word_hits(text,lm) for n,lm in lms.items()},'transfer':{}}
                        for p,value in held.items():
                            t=transfer(value,period,candidate)
                            t['metrics']={n:language_metrics(t['plaintext'],lm) for n,lm in lms.items()}
                            t['word_hits']={n:word_hits(t['plaintext'],lm) for n,lm in lms.items()}
                            row['transfer'][p]=t
                        if oracle is not None:
                            audit=evaluator(oracle)
                            if audit.payload.get('plaintext')!=truth:
                                raise AssertionError('independent encoder/decoder disagreement')
                            row['calibration']={'truth':truth,'oracle_loss':audit.loss,
                                'oracle_candidate':oracle.data,'recovery':recovery_metrics(text,truth)}
                        rows.append(row);write_json(output/'rows'/f'{len(rows):03}.json',row)
                        print('RESULT',len(rows),round(best['loss'],3),row.get('calibration',{}).get('recovery',''),flush=True)
        evidence={'plan':plan,'pages':pages,'runs':rows,'total_evaluations':sum(r['evaluations'] for r in rows)}
        write_json(output/'evidence.json',evidence);return evidence
    finally:engine.dispose()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--budget',type=int,default=4096)
    args=parser.parse_args();run(args.output,args.budget)
