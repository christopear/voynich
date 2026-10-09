"""Post-hoc frozen-key diagnostic of page versus paragraph state resets.

No optimizer or key selection runs here. The ambiguity was noticed after the
initialization experiment; this is not preregistered confirmatory evidence.
"""
import argparse
from pathlib import Path
import re

from voynich.decipher_search.core import LanguageModel
from voynich.laboratory.manifest import file_hash,fingerprint
from voynich.laboratory.medical_recovery import sources
from voynich.laboratory.rotation_pilot import page_lines
from voynich.laboratory.voynich_pilot import language_metrics
from voynich.paths import ROOT
from voynich.storage.artifacts import read_json,write_json


def paragraph_states(length,starts):
    if not starts or starts[0]!=0 or starts!=sorted(set(starts)) or any(i<0 or i>=length for i in starts):
        raise ValueError('ordered paragraph starts must begin at line zero')
    last=0;states=[]
    for i in range(length):
        if i in starts:last=i
        states.append((i-last)%2)
    return states


def decode_states(lines,states,key):
    if len(lines)!=len(states) or any(s not in (0,1) for s in states):raise ValueError('invalid state schedule')
    out=[];known=total=0
    for line,state in zip(lines,states):
        value=[]
        for c in line:
            if c==' ':value.append(' ');continue
            code=chr(ord(c)+state*65536);total+=1;known+=code in key
            value.append(key.get(code,'?'))
        if line.strip():out.append(''.join(value))
    return {'plaintext':' '.join(out),'coverage':known/total}


def common_mask(left,right):
    a,b=left.split(),right.split()
    if len(a)!=len(b):raise ValueError('unaligned plaintext word slots')
    common=[('?' not in x and '?' not in y) for x,y in zip(a,b)]
    return (' '.join(x if keep else '?' for x,keep in zip(a,common)),
            ' '.join(y if keep else '?' for y,keep in zip(b,common)),sum(common))


def audit(evidence,previous,path):
    if file_hash(path)!=previous['plan']['transcription_sha256']:raise ValueError('transcription changed')
    pages=previous['pages'];starts={p:[] for p in pages}
    for line in path.read_text().splitlines():
        match=re.match(r'^<([^,>]+),[^>]*>\s*(.*)$',line)
        if match and '<%>' in match[2]:
            for p,page in pages.items():
                if match[1] in page['loci']:starts[p].append(page['loci'].index(match[1]))
    schedules={p:paragraph_states(len(page['loci']),starts[p]) for p,page in pages.items()}
    source=sources()['pliny'];begin=int(.3*len(source['text']));training=source['text'][begin:begin+60000]
    lm=LanguageModel(training,4);rows=[]
    for row in evidence['rows']:
        if row['case']!='voynich' or row['control']!='original':continue
        for p,page in pages.items():
            lines=page_lines(page);key=row['candidate']['key']
            page_decode=decode_states(lines,[i%2 for i in range(len(lines))],key)
            para_decode=decode_states(lines,schedules[p],key)
            a,b,n=common_mask(page_decode['plaintext'],para_decode['plaintext'])
            rows.append({'seed':row['seed'],'variant':row['variant'],'page':p,'run_ids':row['run_ids'],
                'page_clock':page_decode,'paragraph_clock':para_decode,'common_known_words':n,
                'page_clock_metrics':language_metrics(a,lm),'paragraph_clock_metrics':language_metrics(b,lm),
                'schedules_identical':schedules[p]==[i%2 for i in range(len(lines))]})
    return {'scope':'Post-hoc frozen-key diagnostic; no optimization, no selection on transfer. Not a calibrated clock test.',
            'transcription_hash':file_hash(path),'training_hash':fingerprint(training),
            'paragraph_start_line_indices':starts,'paragraph_states':schedules,'rows':rows}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();write_json(args.output,audit(read_json(args.input),read_json(args.previous),ROOT/'data/ZL3b-n.txt'))
