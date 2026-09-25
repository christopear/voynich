"""Small explicit generators and frozen diagnostics for the mechanism benchmark.

Naibbe table adaptation uses Michael A. Greshko's published tables, preserved
with their source and license in data/mechanisms. It is not the card-deck cipher.
"""
from __future__ import annotations
import csv
import math
import random
import re
import unicodedata
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np
from voynich_core import eva_glyphs

ROOT=Path(__file__).resolve().parents[1]
CALIBRATION_SCALES={'length_mean':.5,'length_sd':.5,'ttr':.05,'hapax':.08,'internal_h':.15,'edge_mi':.025}
DIAGNOSTICS=['edge_short_minus_long','edge_line_minus_ordinary']+[f'{what}_{lag}' for what in ('repeat','edit') for lag in (1,2,4,8,16)]
CLASSES=('assembly','copy','encoding')


@lru_cache(maxsize=50000)
def gl(word):return tuple(eva_glyphs(word))


def clean_plain(text):
    text=unicodedata.normalize('NFKD',text.lower()).replace('æ','ae').replace('œ','oe')
    text=''.join(c for c in text if 'a'<=c<='z')
    return text.replace('j','i').replace('k','c').replace('w','uu')


class Weighted:
    def __init__(self,counts):
        self.values=tuple(counts)
        total=0.;self.cum=[]
        for v in self.values:total+=counts[v];self.cum.append(total)
    def sample(self,rng):return rng.choices(self.values,cum_weights=self.cum,k=1)[0]


class Training:
    def __init__(self,lines):
        self.words=[w['word'] for ln in lines for w in ln['words'] if w['clean']]
        self.lex=Weighted(Counter(self.words));self.lengths=Weighted(Counter(len(gl(w)) for w in self.words))
        chars=Counter(g for w in self.words for g in gl(w));self.chars=Weighted(chars)
        self.transitions=defaultdict(Counter)
        for w in self.words:
            seq=('^','^')+gl(w)
            for i in range(2,len(seq)):
                self.transitions[seq[i-2:i]][seq[i]]+=1
                self.transitions[seq[i-1:i]][seq[i]]+=1
        self.transitions={k:Weighted(v) for k,v in self.transitions.items()}
        edge=defaultdict(Counter);first=Counter()
        for ln in lines:
            for i,kind in enumerate(ln['gaps']):
                a,b=ln['words'][i:i+2]
                if kind=='ordinary' and a['clean'] and b['clean']:
                    edge[gl(a['word'])[-1]][gl(b['word'])[0]]+=1
                    first[gl(b['word'])[0]]+=1
        total=sum(first.values());alphabet=set(chars)
        self.edge={}
        for end,c in edge.items():
            n=sum(c.values())
            for initial in alphabet:
                prior=(first[initial]+.5)/(total+.5*len(alphabet))
                ratio=((c[initial]+5*prior)/(n+5))/prior
                self.edge[(end,initial)]=min(5.,max(.2,ratio))

    def fresh(self,rng):
        n=min(20,max(1,self.lengths.sample(rng)));seq=['^','^']
        for _ in range(n):
            dist=self.transitions.get(tuple(seq[-2:]),self.transitions.get(tuple(seq[-1:]),self.chars))
            seq.append(dist.sample(rng))
        return ''.join(seq[2:])


class Encoder:
    """Invertible normalized-letter stream encoding with explicit unit spaces.

    Enumerate all code strings first, reject any mapping to multiple plaintext
    units. Weighted independent alternatives replace the historical deck draw.
    """
    def __init__(self,path):
        with path.open(encoding='utf-8-sig') as stream:
            rows=list(csv.DictReader(stream))
        weights={'alpha':28,'beta1':14,'beta2':11,'beta3':11,'gamma1':7,'gamma2':7}
        bystate=defaultdict(list);catalog=defaultdict(set);raw=defaultdict(Counter)
        for r in rows:
            state,table,letter=r['code'].split('_');w=r['glyphs']
            bystate[state].append((letter,w,weights[table]))
            if state=='unigram':catalog[w].add(letter);raw[letter][w]+=weights[table]
        # Reserve unigram strings, as in the published ambiguity guard. A
        # bigram may not borrow a reserved unigram output even if it would
        # otherwise create a useful alternative. This preserves single letters.
        reserved=set(catalog)
        for a,x,wa in bystate['prefix']:
            for b,y,wb in bystate['suffix']:
                if x+y in reserved:continue
                catalog[x+y].add(a+b);raw[a+b][x+y]+=wa*wb
        self.reverse={w:next(iter(v)) for w,v in catalog.items() if len(v)==1}
        self.options={p:{w:n for w,n in opts.items() if self.reverse.get(w)==p} for p,opts in raw.items()}
        self.options={p:opts for p,opts in self.options.items() if opts}
        self.letters={p for p in self.options if len(p)==1}
    def decode(self,words):return ''.join(self.reverse[w] for w in words)


def configurations():
    for mechanism in CLASSES:
        for level in range(3):
            for coupling in (0,1):
                yield dict(mechanism=mechanism,level=level,coupling=coupling)


def generate(training,encoder,plain,n,config,seed):
    rng=random.Random(seed);out=[];units=[];position=rng.randrange(max(1,len(plain)//3))
    start=position;level=config['level'];mechanism=config['mechanism']
    mixtures=(0.,.5,.9);windows=(8,32,128);mutation=(.15,.35,.6);single=(.35,.5,.65)
    distributions={}
    if mechanism=='encoding':
        assert set(plain)<=encoder.letters
        power=(.5,1.,2.)[level]
        distributions={p:Weighted({w:v**power for w,v in opts.items()}) for p,opts in encoder.options.items()}
    for _ in range(n):
        unit=None
        if mechanism=='encoding':
            # Circular source is long enough for our runs; wrap is recorded below.
            a=plain[position%len(plain)];b=plain[(position+1)%len(plain)]
            unit=a if rng.random()<single[level] or a+b not in distributions else a+b
            position+=len(unit);units.append(unit)
        def proposal():
            if mechanism=='encoding':return distributions[unit].sample(rng)
            if mechanism=='assembly':
                return training.lex.sample(rng) if rng.random()<mixtures[level] else training.fresh(rng)
            if not out or rng.random()<.2:return training.lex.sample(rng)
            word=list(gl(rng.choice(out[max(0,len(out)-windows[level]):])))
            if rng.random()<mutation[level]:
                pos=rng.randrange(len(word));op=rng.randrange(3)
                if op==0 and len(word)>1:word.pop(pos)
                elif op==1 and len(word)<20:word.insert(pos,training.chars.sample(rng))
                else:word[pos]=training.chars.sample(rng)
            return ''.join(word)
        # Same bounded context-selection opportunity for each mechanism.
        if out and config['coupling']:
            candidates=[proposal() for _ in range(6)];last=gl(out[-1])[-1]
            word=rng.choices(candidates,weights=[training.edge.get((last,gl(w)[0]),1.) for w in candidates],k=1)[0]
        else:word=proposal()
        out.append(word)
    audit={'seed':seed,'n':n,'source_wraps':(position//len(plain)-start//len(plain)) if mechanism=='encoding' else 0}
    if mechanism=='encoding':
        decoded=encoder.decode(out);expected=''.join(units)
        assert decoded==expected
        assert expected==''.join(plain[i%len(plain)] for i in range(start,position))
        audit.update(decoded_characters=len(decoded),roundtrip=True,source_start=start,source_end=position)
    return out,audit


def apply_template(lines,words):
    it=iter(words);out=[]
    for ln in lines:
        out.append(dict(ln,words=[dict(w,word=next(it)) for w in ln['words']]))
    try:next(it);raise AssertionError('unused tokens')
    except StopIteration:pass
    return out


def mi(pairs):
    if not pairs:return 0.
    joint=Counter(pairs);a=Counter(x for x,y in pairs);b=Counter(y for x,y in pairs);n=len(pairs)
    return sum(c/n*math.log2(c*n/(a[x]*b[y])) for (x,y),c in joint.items())


def corrected_mi(records):
    # Within-page shuffles preserve page-specific marginal distributions.
    if len(records)<20:return 0.
    pairs=[(a,b) for a,b,page in records];groups=defaultdict(list)
    for i,(_,_,page) in enumerate(records):groups[page].append(i)
    rng=random.Random(38117);null=[]
    for _ in range(12):
        right=[b for a,b in pairs]
        for inds in groups.values():
            vals=[right[i] for i in inds];rng.shuffle(vals)
            for i,v in zip(inds,vals):right[i]=v
        null.append(mi([(a,right[i]) for i,(a,b) in enumerate(pairs)]))
    return mi(pairs)-float(np.mean(null))


@lru_cache(maxsize=200000)
def edit_similarity(a,b):
    if a==b:return 1.
    ga,gb=gl(a),gl(b);prev=list(range(len(gb)+1))
    for i,x in enumerate(ga,1):
        cur=[i]
        for j,y in enumerate(gb,1):cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
        prev=cur
    return 1-prev[-1]/max(len(ga),len(gb))


def fingerprint(lines):
    words=[w['word'] for ln in lines for w in ln['words'] if w['clean']]
    counts=Counter(words);length=np.array([len(gl(w)) for w in words]);inside=[]
    for w in words:inside.extend(zip(gl(w)[:-1],gl(w)[1:]))
    joint=Counter(inside);left=Counter(a for a,b in inside);n=len(inside)
    internal=-sum(c/n*math.log2(c/left[a]) for (a,b),c in joint.items()) if n else 0.
    ordinary=[];short=[];long=[];linepairs=[];pages=defaultdict(list)
    def edge(a,b,page,target):
        if a['clean'] and b['clean'] and len(gl(a['word']))>=2 and a['word'][-1] in 'nlr':
            r=(a['word'][-1],gl(b['word'])[0],page);target.append(r)
            if target is ordinary:(short if len(gl(a['word'][:-1]))<=2 else long).append(r)
    for j,ln in enumerate(lines):
        page=ln['page'];pages[page].extend(w['word'] if w['clean'] else None for w in ln['words'])
        for i,kind in enumerate(ln['gaps']):
            if kind=='ordinary':edge(*ln['words'][i:i+2],page,ordinary)
        if j+1<len(lines):
            nxt=lines[j+1]
            if page==nxt['page'] and nxt['number']==ln['number']+1 and not ln['paragraph_end'] and not nxt['paragraph_start']:
                edge(ln['words'][-1],nxt['words'][0],page,linepairs)
    baseline=corrected_mi(ordinary)
    d={'length_mean':float(length.mean()),'length_sd':float(length.std()),'ttr':len(counts)/len(words),
       'hapax':sum(n==1 for n in counts.values())/len(counts),'internal_h':internal,'edge_mi':baseline,
       'edge_short_minus_long':corrected_mi(short)-corrected_mi(long),
       'edge_line_minus_ordinary':corrected_mi(linepairs)-baseline,
       'tokens':len(words),'short_n':len(short),'long_n':len(long),'line_n':len(linepairs)}
    # Lag pairs stay within a page and cannot bridge an illegible token. Line
    # transitions remain in the sequence. All separator classes count as slots.
    for lag in (1,2,4,8,16):
        pairs=[];rep_expected=0.;npairs=0
        for page,seq in pages.items():
            clean=[w for w in seq if w is not None];c=Counter(clean);nn=len(clean)
            collision=sum(v*(v-1) for v in c.values())/max(1,nn*(nn-1))
            eligible=[(seq[i],seq[i+lag],page) for i in range(len(seq)-lag) if all(w is not None for w in seq[i:i+lag+1])]
            pairs.extend(eligible);rep_expected+=collision*len(eligible);npairs+=len(eligible)
        d[f'repeat_{lag}']=(sum(a==b for a,b,p in pairs)-rep_expected)/max(1,npairs)
        rng=random.Random(173+lag);sample=rng.sample(pairs,min(512,len(pairs)))
        similarities=[];null=[]
        for a,b,page in sample:
            similarities.append(edit_similarity(a,b))
            pool=[w for w in pages[page] if w is not None]
            null.append(edit_similarity(a,rng.choice(pool)))
        d[f'edit_{lag}']=float(np.mean(similarities)-np.mean(null)) if sample else 0.
        d[f'lag_n_{lag}']=npairs
    return d


def calibration_distance(a,b):
    return float(np.mean([((a[k]-b[k])/scale)**2 for k,scale in CALIBRATION_SCALES.items()]))
