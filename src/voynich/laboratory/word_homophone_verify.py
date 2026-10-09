"""Replay complete forward ciphertexts and independently check retained summaries."""
import argparse
from collections import Counter
import json
from pathlib import Path
from voynich.experiments.e28_word_homophones import GRID,encrypt,metrics,save
from voynich.experiments.e27_unit_association import sha
from voynich.paths import ROOT


def verify(folder):
    read=lambda name:json.loads((folder/name).read_text())
    e=read('evidence.json');panels=read('source_panels.json');keys=read('codebooks.json');slots=read('slots.json')
    manifest=read('manifest.json')
    for path,digest in manifest['hashes'].items():assert sha(ROOT/path)==digest,path
    seen=set();count=0
    for r in e['records']:
        identity=(r['source'],r['split'],r['passage_seed'],r['configuration'],r['encoding_seed'])
        assert identity not in seen;seen.add(identity)
        panel=next(p for p in panels[r['source']] if p['seed']==r['passage_seed'])
        probability=GRID[r['configuration']];key=keys[r['source']][str(len(probability))]
        assert encrypt(panel['words'],key,probability,r['encoding_seed'])==r['tokens']
        decoder={c:w for w,cs in key.items() for c in cs}
        assert [decoder[c] for c in r['tokens']]==panel['words']
        c=Counter(r['tokens']);assert len(c)/1024==r['metrics']['ttr']
        assert sum(n for _,n in c.most_common(10))/1024==r['metrics']['top10']
        count+=1
    assert count==504
    for name,rows in slots.items():assert metrics([r['word'] for r in rows],rows)==e['targets'][name]
    for name,pp in panels.items():
        a={s['chapter'] for p in pp if p['split']=='development' for s in p['spans']}
        b={s['chapter'] for p in pp if p['split']=='validation' for s in p['spans']}
        assert not a&b
    assert not {r['folio'] for r in slots['ZL_original']}&{r['folio'] for r in slots['ZL_additional']}
    result=dict(ciphertext_panels_replayed=count,word_tokens_roundtripped=count*1024,
        manuscript_panels_recomputed=len(slots),chapter_and_folio_separation='verified',
        evidence_sha256=sha(folder/'evidence.json'),status='passed')
    save(folder/'verification.json',result);print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,default=ROOT/'results/word_homophones_2026-10-09')
    verify(p.parse_args().directory)
