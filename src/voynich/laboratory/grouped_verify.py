"""Replay registered grouped results and independently decode synthetic fixtures."""
import argparse
from pathlib import Path
import string

from voynich.ciphers.units import UnitCipher
from voynich.ciphers.models import CipherKey
from voynich.decipher_search.core import normalize, digest
from voynich.laboratory.manifest import fingerprint, file_hash
from voynich.paths import ROOT
from voynich.search.grouped import GroupedProblem, GroupedEvaluator, screen_policies
from voynich.search.codebooks import CodebookSearch
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import read_json, write_json
from voynich.storage.database import make_engine
from voynich.storage.registry import Registry


def verify(directory,output):
    evidence=read_json(directory/'evidence.json');specs=read_json(directory/'specifications.json')
    env=read_json(directory/'environment.json')
    for path,digest_value in env['source_hashes'].items():
        if file_hash(ROOT/path)!=digest_value:raise AssertionError('execution source changed: '+path)
    paths={'celsus':ROOT/'data/laboratory_sources/celsus_medical.txt',
           'pliny':ROOT/'data/laboratory_sources/pliny_medical.txt','dante':ROOT/'data/italian_dante.txt'}
    for name,value in evidence['plan']['source_hashes'].items():
        if file_hash(paths[name])!=value:raise AssertionError('source changed')
    if file_hash(ROOT/'data/ZL3b-n.txt')!=evidence['plan']['transcription_hash']:raise AssertionError('transcription changed')
    by_id={fingerprint(s):s for s in specs};rows={r['id']:r for r in evidence['rows']}
    engine=make_engine();registry=Registry(engine);replayed=bindings=records=roundtrips=0
    try:
        for stage in evidence['stages']:
            spec=by_id[stage['spec_id']];row=rows[stage['case_id']]
            ref=next(d for d in spec['datasets'] if d['role']=='training')
            training=normalize(paths[ref['source_id']].read_text())[ref['start']:ref['stop']]
            if digest(training)!=ref['prepared_hash']:raise AssertionError('training mismatch')
            p=GroupedProblem(tuple(row['spans']),training,tuple(spec['configuration']['policy']['prefixes']),row['spacing'])
            e=GroupedEvaluator(p);strategy=CodebookSearch(p,algorithm='beam',seed=row['seed'],width=8,budget=4096)
            binding=fingerprint({'strategy':strategy.identity(),'evaluator':e.identity(),'batch_size':8})
            if binding!=spec['configuration']['execution_binding']:raise AssertionError('binding mismatch')
            bindings+=1
            stored=registry.get(stage['run_id'])
            if stored['spec_id']!=stage['spec_id'] or stored['sequence']!=4096 or stored['stop_reason']!='evaluation-limit':raise AssertionError('registry mismatch')
            if stored['checkpoint']['failures']:raise AssertionError('evaluator exception')
            if stored['checkpoint']['top']!=stage['top']:raise AssertionError('retention mismatch')
            records+=1
            for best in stage['top']:
                replay=e(Candidate.create(**best['candidate']))
                if replay.loss!=best['loss'] or replay.payload!=best['payload']:raise AssertionError('replay mismatch')
                replayed+=1
        for row in evidence['rows']:
            if row['kind']!='synthetic':continue
            c=row['calibration'];method=UnitCipher('groups',homophones=2,lengths='variable',spacing=row['spacing'],alphabet=string.ascii_uppercase[:16])
            key=CipherKey(method.method_id,tuple(c['oracle_table'].items()))
            for span,truth in zip(row['spans'],c['truth_spans']):
                result=method.decrypt_text(span if row['spacing']=='preserve' else span.replace(' ',''),key)
                if result.plaintexts!=(truth,) or not result.complete:raise AssertionError('independent trie roundtrip mismatch')
                roundtrips+=1
        result={'database_records_verified':records,'execution_bindings_verified':bindings,
                'retained_candidates_replayed':replayed,'independent_trie_roundtrip_spans':roundtrips,
                'execution_source_hashes_verified':len(env['source_hashes']),'execution_commit':env['git_commit'],
                'execution_dirty':env['git_dirty'],'verdict':'All requested checks passed'}
        write_json(output,result);print(result);return result
    finally:engine.dispose()

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--directory',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();verify(args.directory,args.output)
