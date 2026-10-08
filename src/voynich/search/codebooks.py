"""Bounded codebook search with explicit, prefix-determined segmentation.

Unlike the legacy strategy, a two-character code need not have character-level
fallback entries. Boundaries are determined by a declared width or a searched
set of two-character prefixes. This is a restricted family, not all segmentations.
"""
from collections import Counter
from dataclasses import asdict, dataclass
import math
import random
import string

from voynich.decipher_search.core import key_bits
from voynich.evaluation.outcomes import ScoreReport
from voynich.evaluation.scorers import Evaluation, model
from voynich.laboratory.fixtures import PublicInput
from voynich.laboratory.manifest import canonical, fingerprint, stream_seed
from voynich.search.strategies import Candidate, tuples


def tokenize(ciphertext, width=1, long_prefixes=()):
    if width not in (None,1,2):
        raise ValueError('supported widths: 1, 2, or prefix-determined')
    long_prefixes=set(long_prefixes)
    result=[]
    pos=0
    while pos<len(ciphertext):
        if ciphertext[pos]==' ':
            result.append((' ',pos,pos+1));pos+=1;continue
        size=width if width is not None else (2 if ciphertext[pos] in long_prefixes else 1)
        code=ciphertext[pos:pos+size]
        if len(code)!=size or ' ' in code:
            raise ValueError('code crosses a word boundary or input end')
        result.append((code,pos,pos+size));pos+=size
    return result


@dataclass(frozen=True)
class CodebookProblem:
    public: PublicInput
    training: str
    units: tuple[str,...]=tuple(string.ascii_lowercase)
    width: int | None=1
    capacity: int=1
    order: int=4

    def __post_init__(self):
        if self.public.spacing!='preserve' or self.width not in (None,1,2):
            raise ValueError('only preserved-word-space bounded codes are supported')
        if self.capacity not in (1,2) or not self.units or len(set(self.units))!=len(self.units):
            raise ValueError('invalid unit inventory/capacity')
        if any(not u or any(c not in string.ascii_lowercase for c in u) for u in self.units):
            raise ValueError('units must be nonempty lowercase letters')
        if not 1<=self.order<=6:
            raise ValueError('invalid language model order')

    def identity(self):
        return {'public':asdict(self.public),'training_hash':fingerprint(self.training),
            'units':self.units,'width':self.width,'capacity':self.capacity,'order':self.order}

    def tokens(self,candidate):
        return tokenize(self.public.ciphertext,self.width,candidate.data.get('long_prefixes',()))


@dataclass(frozen=True)
class CodebookEvaluator:
    problem: CodebookProblem

    def identity(self):
        return {'evaluator':'explicit-codebook-v1','problem':self.problem.identity(),
                'deterministic':True,'selection':'language+uniform-choice+codebook+prefix-description'}

    def __call__(self,candidate):
        p=self.problem;data=candidate.data;key=data['key']
        denominator=max(1,len(p.public.ciphertext.replace(' ','')))
        invalid=lambda:Evaluation(ScoreReport('explicit-codebook-v1',(),denominator,0,False),{},'invalid')
        if not key or any(u not in p.units for u in key.values()):
            return invalid()
        counts=Counter(key.values())
        if max(counts.values())>p.capacity:
            return invalid()
        try:tokens=p.tokens(candidate)
        except ValueError:return invalid()
        # Exact inventory: no unused fallback codes affect choice probabilities.
        if set(key)!={code for code,_,_ in tokens if code!=' '}:
            return invalid()
        out=[]
        for code,a,b in tokens:
            if code==' ':out.append(' ');continue
            unit=key[code]
            if len(unit)>2 and ((a and p.public.ciphertext[a-1]!=' ') or
                               (b<len(p.public.ciphertext) and p.public.ciphertext[b]!=' ')):
                return invalid()
            out.append(unit)
        plain=''.join(out)
        lm=model(p.training,p.order)
        language=lm.nll(plain)
        choices=sum(math.log2(counts[key[c]]) for c,_,_ in tokens if c!=' ')
        complexity=key_bits(key,len(p.units),len(set(p.public.ciphertext)-{' '}))
        prefix_bits=len(set(p.public.ciphertext)-{' '}) if p.width is None else 0
        score=ScoreReport('explicit-codebook-v1',(('language_bits',language),('encoding_choice_bits',choices),
            ('key_bits',complexity),('prefix_policy_bits',float(prefix_bits))),denominator)
        return Evaluation(score,{'plaintext':plain,'tokens':[c for c,_,_ in tokens]})


def partial_transfer(problem,candidate):
    """Frozen mappings only; return unknown markers without fitting new symbols."""
    try:tokens=problem.tokens(candidate)
    except ValueError:
        return {'valid_segmentation':False,'plaintext':'','code_token_coverage':0,
                'cipher_character_coverage':0,'unknown_codes':[]}
    key=candidate.data['key'];out=[];unknown=[];covered=total=covered_chars=total_chars=0
    for code,_,_ in tokens:
        if code==' ':out.append(' ');continue
        total+=1;total_chars+=len(code)
        if code in key:
            out.append(key[code]);covered+=1;covered_chars+=len(code)
        else:out.append('?');unknown.append(code)
    return {'valid_segmentation':True,'plaintext':''.join(out),'code_token_coverage':covered/max(1,total),
        'cipher_character_coverage':covered_chars/max(1,total_chars),'unknown_codes':sorted(set(unknown)),
        'interpretation':'Question marks count as errors; mappings and segmentation policy frozen.'}


class CodebookSearch:
    """Paired annealing or diversity-filtered beam over complete codebooks.

    Both algorithms receive the same initial candidates and mutation operator.
    Beam keeps the best candidate and prefers keys separated by >=2 assignments;
    this does not certify exhaustive search or optimality.
    """
    def __init__(self,problem,*,algorithm='annealing',seed=7,width=8,budget=8000):
        if problem.public.role!='development':
            raise ValueError('reserved inputs cannot drive adaptive search')
        if algorithm not in {'annealing','beam'} or width<1 or budget<width:
            raise ValueError('invalid search settings')
        self.problem=problem;self.algorithm=algorithm;self.seed=seed;self.width=width;self.budget=budget
        self.rng=random.Random(stream_seed(seed,'codebooks','search'))
        self.cursor=0;self.evaluated=0;self.invalid=0;self.pending=[]
        lm=model(problem.training,problem.order)
        self.ranked_units=sorted(problem.units,key=lambda u:(-lm.text.count(u),u))
        self.pool=[]
        for i in range(width):
            prefixes=[]
            if problem.width is None and i%2:
                prefixes=sorted(set(problem.public.ciphertext)-{' '})
                try:tokenize(problem.public.ciphertext,None,prefixes)
                except ValueError:prefixes=[]
            candidate=self._make({},prefixes,shuffle=i!=0)
            self.pool.append({'candidate':candidate.data,'loss':None})

    def identity(self):
        return {'strategy':'bounded-codebook-'+self.algorithm+'-v1','problem':self.problem.identity(),
            'seed':self.seed,'width':self.width,'budget':self.budget,'diversity_min_assignments':2,
            'temperature_total_bits':[12,.2]}

    def _make(self,key,prefixes,shuffle=False):
        p=self.problem
        tokens=tokenize(p.public.ciphertext,p.width,prefixes)
        frequency=Counter(c for c,_,_ in tokens if c!=' ')
        key={c:u for c,u in key.items() if c in frequency}
        used=Counter(key.values())
        # Multi-letter word units are permissible only for whole ciphertext words.
        whole={c:all((a==0 or p.public.ciphertext[a-1]==' ') and
                    (b==len(p.public.ciphertext) or p.public.ciphertext[b]==' ')
                    for token,a,b in tokens if token==c) for c in frequency}
        available=[u for u in self.ranked_units for _ in range(p.capacity-used[u])]
        if shuffle:self.rng.shuffle(available)
        for c in sorted(frequency,key=lambda c:(-frequency[c],c)):
            if c in key:continue
            allowed=[i for i,u in enumerate(available) if len(u)<=2 or whole[c]]
            if not allowed:
                raise ValueError('observed code inventory exceeds declared emission capacity')
            key[c]=available.pop(allowed[0])
        return Candidate.create('explicit-codebook-v1',key=key,long_prefixes=sorted(prefixes))

    def _mutate(self,parent):
        data=parent['candidate'];key=dict(data['key']);prefixes=set(data.get('long_prefixes',()))
        if self.problem.width is None and self.rng.random()<.2:
            c=self.rng.choice(sorted(set(self.problem.public.ciphertext)-{' '}))
            prefixes.symmetric_difference_update({c})
            try:return self._make(key,prefixes,shuffle=True)
            except ValueError:return Candidate.create(**{'method':data['method'],'key':key,
                    'long_prefixes':sorted(prefixes)}) # Invalid structural proposal is scored/countable.
        if len(key)>1 and self.rng.random()<.75:
            a,b=self.rng.sample(list(key),2);key[a],key[b]=key[b],key[a]
        else:
            c=self.rng.choice(list(key));counts=Counter(key.values());counts[key[c]]-=1
            units=[u for u in self.problem.units if counts[u]<self.problem.capacity]
            key[c]=self.rng.choice(units)
        return Candidate.create('explicit-codebook-v1',key=key,long_prefixes=sorted(prefixes))

    def propose(self,limit):
        if self.pending:raise RuntimeError('feedback required before another batch')
        count=min(limit,self.width,self.budget-self.evaluated)
        if self.evaluated<self.width:
            count=min(count,self.width-self.evaluated)
        if count<=0:return []
        for _ in range(count):
            i=self.cursor%len(self.pool);self.cursor+=1
            parent=self.pool[i]
            candidate=Candidate(canonical(parent['candidate'])) if self.evaluated<self.width else self._mutate(parent)
            self.pending.append((i,candidate))
        return [c for _,c in self.pending]

    @staticmethod
    def distance(a,b):
        ak,bk=a['candidate']['key'],b['candidate']['key']
        return sum(ak.get(c)!=bk.get(c) for c in set(ak)|set(bk))+len(
            set(a['candidate'].get('long_prefixes',()))^set(b['candidate'].get('long_prefixes',())))

    def observe(self,results):
        if len(results)!=len(self.pending):raise ValueError('feedback mismatch')
        proposals=[]
        for (index,candidate),value in zip(self.pending,results):
            self.invalid+=value.loss is None
            score=value.loss*value.denominator if value.loss is not None else None
            item={'candidate':candidate.data,'loss':score}
            initial=self.evaluated<self.width
            if initial:self.pool[index]=item
            elif self.algorithm=='annealing':
                previous=self.pool[index]['loss']
                temperature=12*(.2/12)**(self.evaluated/max(1,self.budget-1))
                if score is not None and (previous is None or score<=previous or
                    self.rng.random()<2**(-(score-previous)/temperature)):
                    self.pool[index]=item
            elif score is not None:proposals.append(item)
            self.evaluated+=1
        if self.algorithm=='beam' and proposals:
            unique={canonical(x['candidate']):x for x in self.pool+proposals if x['loss'] is not None}
            ranked=sorted(unique.values(),key=lambda x:(x['loss'],canonical(x['candidate'])))
            kept=[]
            for row in ranked:
                if all(self.distance(row,other)>=2 for other in kept):kept.append(row)
                if len(kept)==self.width:break
            for row in ranked:
                if len(kept)==self.width:break
                if row not in kept:kept.append(row)
            self.pool=kept or self.pool
        self.pending=[]

    def diagnostics(self):
        return {'invalid_candidates':self.invalid,'evaluated':self.evaluated,
            'final_total_costs':[x['loss'] for x in self.pool],
            'scope':'final states, not per-chain optima; invalid proposals count against budget'}

    def snapshot(self):
        if self.pending:raise RuntimeError('checkpoint requires consumed feedback')
        import json
        return json.loads(canonical({'schema':1,'identity':fingerprint(self.identity()),'pool':self.pool,
            'rng':self.rng.getstate(),'cursor':self.cursor,'evaluated':self.evaluated,'invalid':self.invalid}))

    def restore(self,state):
        if state.get('schema')!=1 or state.get('identity')!=fingerprint(self.identity()):
            raise ValueError('incompatible codebook checkpoint')
        self.pool=state['pool'];self.cursor=state['cursor'];self.evaluated=state['evaluated']
        self.invalid=state['invalid'];self.rng.setstate(tuples(state['rng']));self.pending=[]
