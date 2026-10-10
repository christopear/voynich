"""Transcription-only zodiac label inventory for scoping, not a crib search."""
import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from voynich.experiments.e06_boundary_frontier import parse_body
from voynich.paths import ROOT


def inventory(path):
    rows=[]; meta={}
    for line in path.read_text().splitlines():
        header=re.match(r'^<(f[^.> ]+)>\s*<!([^>]*)>',line)
        if header:
            meta[header[1]]=dict(re.findall(r'\$(\w)=([^\s>]+)',header[2]))
        match=re.match(r'^<(f[^.>]+)\.(\d+),([^>]*)>\s*(.*)$',line)
        if not match or match[3][1:]!='Lz' or meta.get(match[1],{}).get('I')!='Z':
            continue
        words,gaps=parse_body(match[4])
        rows.append(dict(locus=f'{match[1]}.{match[2]}',page=match[1],
            folio=re.match(r'f\d+',match[1])[0],raw=match[4],
            clean=all(w['clean'] for w in words),tokens=[w['word'] for w in words],gaps=gaps,
            metadata=meta[match[1]],facsimile_alignment='not yet independently verified'))
    labels=defaultdict(list)
    for row in rows:
        if row['clean']:
            labels[tuple(row['tokens'])].append(row['locus'])
    repeated=[dict(tokens=list(k),loci=v) for k,v in labels.items()
              if len({locus.split('.')[0] for locus in v})>1]
    return dict(status='scope inventory, no semantic assignments or decipherment',
        source=str(path.relative_to(ROOT)),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        page_counts=dict(Counter(r['page'] for r in rows)),labels=len(rows),
        clean_labels=sum(r['clean'] for r in rows),rows=rows,cross_page_exact_repeats=repeated)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=ROOT/'results/crib_scope_2026-10-09')
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    data=inventory(ROOT/'data/ZL3b-n.txt')
    (args.output/'inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print({k:data[k] for k in ('labels','clean_labels','page_counts')})
    print('Cross-page exact repeats:',len(data['cross_page_exact_repeats']))


if __name__=='__main__':
    main()
