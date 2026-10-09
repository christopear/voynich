"""Bounded prefix-determined glyph groups; space decoding is an explicit code.

Reuses the audited codebook beam, but searches mappings AFTER screening parsing
policies. It cannot identify arbitrary variable-length codes or insert spaces.
"""
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
import math
import string

from voynich.decipher_search.core import key_bits
from voynich.evaluation.scorers import Evaluation, model
from voynich.evaluation.outcomes import ScoreReport
from voynich.laboratory.fixtures import PublicInput
from voynich.laboratory.manifest import fingerprint
from voynich.search.codebooks import CodebookSearch, tokenize


def parse_span(text, prefixes, spacing):
    if spacing not in {'preserve', 'encoded'}:
        raise ValueError('unknown spacing policy')
    text = text if spacing == 'preserve' else text.replace(' ', '')
    return [code for code, _, _ in tokenize(text, None, prefixes)]


def screen_policies(spans, training, spacing, keep=4):
    alphabet = sorted(set(''.join(spans)) - {' '})
    units = string.ascii_lowercase + (' ' if spacing == 'encoded' else '')
    counts = Counter(training if spacing == 'encoded' else training.replace(' ', ''))
    probabilities = sorted([counts[u]/max(1,sum(counts.values()))/2 for u in units for _ in range(2)], reverse=True)
    rows = []; stats = Counter()
    policies = [p for n in (1,2,3) for p in combinations(alphabet,n)]
    if tuple(alphabet) not in policies: policies.append(tuple(alphabet))
    for prefixes in policies:
        stats['enumerated'] += 1
        try: parsed = [parse_span(s,prefixes,spacing) for s in spans]
        except ValueError:
            stats['truncated_code'] += 1; continue
        freq = Counter(c for line in parsed for c in line if c != ' ')
        if not freq: stats['empty'] += 1; continue
        expansion = sum(len(c)*n for c,n in freq.items()) / sum(freq.values())
        if not 1.35 <= expansion <= 2:
            stats['expansion_outside_grid'] += 1; continue
        if len(freq) > len(units)*2:
            stats['inventory_over_capacity'] += 1; continue
        # Structural shortlist only; no true key, plaintext or independent scorer.
        cost = -sum(n*math.log2(max(1e-12,p)) for n,p in zip(sorted(freq.values(),reverse=True),probabilities))/sum(freq.values())
        rows.append({'prefixes':list(prefixes),'inventory':len(freq),'expansion':expansion,
                     'unigram_screen_cost':cost})
    rows.sort(key=lambda r:(r['unigram_screen_cost'],r['inventory'],r['prefixes']))
    stats['surviving'] = len(rows)
    return {'counts':dict(stats),'selected':rows[:keep],'survivors':rows}


@dataclass(frozen=True)
class GroupedProblem:
    spans: tuple[str,...]
    training: str
    prefixes: tuple[str,...]
    spacing: str
    capacity: int = 2
    order: int = 4
    width: int = 1

    def __post_init__(self):
        if self.spacing not in {'preserve','encoded'} or not self.spans or self.capacity != 2:
            raise ValueError('unsupported grouped problem')
        parsed = tuple(tuple(parse_span(s,self.prefixes,self.spacing)) for s in self.spans)
        codes = sorted({c for line in parsed for c in line if c != ' '})
        ids = {c:chr(0xF000+i) for i,c in enumerate(codes)}
        encoded = tuple(''.join(' ' if c==' ' else ids[c] for c in line) for line in parsed)
        object.__setattr__(self,'parsed',parsed)
        object.__setattr__(self,'ids',ids)
        object.__setattr__(self,'encoded',encoded)
        object.__setattr__(self,'public',PublicInput(' '.join(encoded),'grouped-prefix-v1','preserve'))
        object.__setattr__(self,'units',tuple(string.ascii_lowercase)+((' ',) if self.spacing=='encoded' else ()))
        if not codes or len(codes)>len(self.units)*self.capacity:
            raise ValueError('empty or excessive code inventory')

    def identity(self):
        return {'family':'grouped-prefix-v1','spans':self.spans,'prefixes':self.prefixes,
                'spacing':self.spacing,'capacity':self.capacity,'training_hash':fingerprint(self.training),'order':self.order}

    def tokens(self,candidate): return tokenize(self.public.ciphertext,1)


class GroupedEvaluator:
    def __init__(self,problem): self.problem=problem

    def identity(self):
        return {'evaluator':'grouped-prefix-v1','problem':self.problem.identity(),
                'selection':'language+homophone-choice+actual-codebook+prefix-policy',
                'context':'reset each line/omission/drawing span','deterministic':True}

    def __call__(self,candidate):
        p=self.problem; key=candidate.data['key']; denom=sum(len(s.replace(' ','')) for s in p.spans)
        invalid=lambda:Evaluation(ScoreReport('grouped-prefix-v1',(),denom,0,False),{},'invalid')
        if set(key)!=set(p.ids.values()) or any(v not in p.units for v in key.values()):return invalid()
        counts=Counter(key.values())
        if max(counts.values())>p.capacity:return invalid()
        table={c:key[i] for c,i in p.ids.items()}
        plain=[''.join(' ' if c==' ' else table[c] for c in line) for line in p.parsed]
        lm=model(p.training,p.order)
        language=sum(lm.nll(s) for s in plain)
        choice=sum(math.log2(counts[table[c]]) for line in p.parsed for c in line if c!=' ')
        alphabet=len(set(''.join(p.spans))-{' '})
        complexity=key_bits(table,len(p.units),alphabet)
        policy=alphabet+math.log2(alphabet+1)
        score=ScoreReport('grouped-prefix-v1',(('language_bits',language),('choice_bits',choice),
                         ('key_bits',complexity),('policy_bits',policy)),denom)
        return Evaluation(score,{'plaintext':'\n'.join(plain),'plaintext_spans':plain,'table':table})


def frozen_decode(spans,prefixes,spacing,table,lm):
    outputs=[]; known=total=valid_spans=full_chars=0; full_cost=known_cost=0.; known_chars=0
    for span in spans:
        total+=len(span.replace(' ',''))
        try:tokens=parse_span(span,prefixes,spacing)
        except ValueError:
            outputs.append({'valid':False,'plaintext':None,'reason':'truncated code'}); continue
        valid_spans+=1
        text=''.join(' ' if c==' ' else table.get(c,'?') for c in tokens)
        known+=sum(len(c) for c in tokens if c!=' ' and c in table)
        outputs.append({'valid':True,'plaintext':text})
        if '?' not in text:
            full_chars+=len(text);full_cost+=lm.nll(text)
        for run in text.split('?'):
            if run:known_chars+=len(run);known_cost+=lm.nll(run)
    return {'spans':outputs,'glyph_coverage':known/max(1,total),'valid_span_fraction':valid_spans/max(1,len(spans)),
            'fully_known_span_characters':full_chars,'fully_known_span_bits_per_character':full_cost/full_chars if full_chars else None,
            'covered_run_characters':known_chars,'covered_run_bits_per_character':known_cost/known_chars if known_chars else None,
            'caveat':'Unknowns reset context; scores with different masks are not paired transfer improvements.'}
