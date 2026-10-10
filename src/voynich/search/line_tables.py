"""Known line-clock substitution hypotheses; independent injective tables.

This tests period one or two, reset at each page's first paragraph-text line.
It does not infer arbitrary state transitions or establish historical usage.
"""
from collections import Counter
import math
import string

from voynich.evaluation.outcomes import ScoreReport
from voynich.evaluation.scorers import Evaluation, model
from voynich.laboratory.fixtures import PublicInput
from voynich.laboratory.manifest import fingerprint
from voynich.search.codebooks import CodebookProblem, CodebookSearch
from voynich.search.strategies import Candidate


def phase_text(lines, period):
    if type(period) is not int or period not in (1, 2):
        raise ValueError('only one or two line tables are implemented')
    if isinstance(lines,str) or not lines or not any(line.strip() for line in lines):
        raise ValueError('nonempty line collection required')
    result = []
    for index, line in enumerate(lines):
        if any(c.isspace() and c != ' ' or ord(c) >= 65536 for c in line):
            raise ValueError('lines require space-delimited BMP symbols')
        # Empty/omitted lines still advance the state clock.
        encoded = ''.join(' ' if c == ' ' else chr(ord(c)+(index % period)*65536) for c in line)
        if encoded.strip():
            result.append(' '.join(encoded.split()))
    return ' '.join(result)


def transfer(lines, period, candidate):
    text = phase_text(lines, period); key = candidate.data['key']
    unknown = sorted(set(text)-set(key)-{' '})
    return {'plaintext': ''.join(' ' if c == ' ' else key.get(c, '?') for c in text),
            'code_token_coverage': sum(c in key for c in text if c != ' ')/len(text.replace(' ', '')),
            'unknown': [{'phase': ord(c)//65536, 'symbol': chr(ord(c)%65536)} for c in unknown]}


class LineTableEvaluator:
    def __init__(self, lines, training, period):
        self.lines, self.training, self.period = tuple(lines), training, period
        self.text = phase_text(lines, period)
        self.codes = set(self.text)-{' '}
        self.denominator = len(self.text.replace(' ', ''))
        if any(sum(ord(c)//65536 == phase for c in self.codes)>26 for phase in range(period)):
            raise ValueError('more than 26 observed symbols in a table')
        self.key_cost = sum(sum(math.log2(26-i) for i in range(sum(ord(c)//65536 == phase for c in self.codes)))
                            for phase in range(period))

    def identity(self):
        return {'evaluator': 'line-table-v1', 'lines': self.lines, 'period': self.period,
                'training_hash': fingerprint(self.training), 'order': 4, 'deterministic': True,
                'selection': 'language bits + log2 injective table count + 1 period bit',
                'clock': 'paragraph-text line index, page reset, fixed phase zero'}

    def __call__(self, candidate):
        key = candidate.data['key']
        valid = set(key) == self.codes and all(u in string.ascii_lowercase and len(u)==1 for u in key.values())
        for phase in range(self.period):
            values = [u for c,u in key.items() if ord(c)//65536 == phase]
            valid &= len(values) == len(set(values))
        if not valid:
            return Evaluation(ScoreReport('line-table-v1', (), self.denominator, 0, False), {}, 'invalid')
        plain = ''.join(' ' if c == ' ' else key[c] for c in self.text)
        score = ScoreReport('line-table-v1', (('language_bits', self.language_bits(key,plain)),
                            ('table_bits', self.key_cost), ('period_bits', 1.)), self.denominator)
        return Evaluation(score, {'plaintext': plain})

    def language_bits(self,key,plain):
        return model(self.training,4).nll(plain)


class SeparateLineEvaluator(LineTableEvaluator):
    """Initialization surrogate: reset n-gram history at each assigned line."""
    def __init__(self,lines,training):
        super().__init__(lines,training,1)

    def identity(self):
        return {**super().identity(),'evaluator':'separate-line-initialization-v1',
                'language_context':'reset at every nonempty line; initialization only'}

    def language_bits(self,key,plain):
        lm=model(self.training,4)
        return sum(lm.nll(''.join(' ' if c==' ' else key[c] for c in ' '.join(line.split())))
                   for line in self.lines if line.strip())


class LineTableSearch(CodebookSearch):
    """Reuse the tested beam/checkpoint machinery, with within-table moves."""
    def __init__(self, lines, training, period, *, seed=7, budget=4096, width=8):
        self.period = period
        public = PublicInput(phase_text(lines, period), 'line-table-v1', 'preserve')
        super().__init__(CodebookProblem(public, training), algorithm='beam', seed=seed, width=width, budget=budget)

    def identity(self):
        return {**super().identity(), 'strategy': 'line-table-beam-v1', 'period': self.period}

    def _make(self, key, prefixes, shuffle=False):
        frequency = Counter(self.problem.public.ciphertext.replace(' ', ''))
        mapping = {}
        for phase in range(self.period):
            codes = sorted((c for c in frequency if ord(c)//65536 == phase), key=lambda c:(-frequency[c],c))
            if len(codes)>26:
                raise ValueError('more than 26 observed symbols in a table')
            units = list(self.ranked_units)
            if shuffle:
                self.rng.shuffle(units)
            mapping.update(zip(codes,units))
        return Candidate.create('line-table-v1', key=mapping)

    def _mutate(self, parent):
        key = dict(parent['candidate']['key'])
        groups = [[c for c in key if ord(c)//65536 == phase] for phase in range(self.period)]
        codes = self.rng.choice([g for g in groups if g])
        if len(codes)>1 and self.rng.random()<.75:
            a,b = self.rng.sample(codes,2); key[a],key[b] = key[b],key[a]
        else:
            c = self.rng.choice(codes)
            used = {key[x] for x in codes if x != c}
            key[c] = self.rng.choice([u for u in self.problem.units if u not in used])
        return Candidate.create('line-table-v1', key=key)


class InitializedLineTableSearch(LineTableSearch):
    """Joint refinement of explicit initial candidates; all rescores count."""
    def __init__(self,lines,training,period,candidates,*,seed=7,budget=4096,width=8):
        if len(candidates)!=width:
            raise ValueError('one explicit candidate per initial beam slot required')
        self.initial_recipes=tuple(c.recipe for c in candidates)
        super().__init__(lines,training,period,seed=seed,budget=budget,width=width)
        codes=set(self.problem.public.ciphertext)-{' '}
        for candidate in candidates:
            key=candidate.data['key']
            if set(key)!=codes or any(len(v)!=1 or v not in string.ascii_lowercase for v in key.values()):
                raise ValueError('initial mapping does not match public cipher inventory')
            for phase in range(period):
                values=[v for c,v in key.items() if ord(c)//65536==phase]
                if len(values)!=len(set(values)):
                    raise ValueError('initial table must be injective')
        self.pool=[{'candidate':c.data,'loss':None} for c in candidates]

    def identity(self):
        return {**super().identity(),'strategy':'initialized-line-table-beam-v1',
                'initial_recipes_hash':fingerprint(self.initial_recipes)}


def combine_phase_winners(results,width=8):
    """Rank the Cartesian product by additive initialization costs, not truth.

    Results are top-retention records from the two single-table phase runs.
    Full-text joint evaluation takes place inside the subsequent counted run.
    """
    from itertools import product
    if len(results)!=2 or any(not rows for rows in results):
        raise ValueError('two nonempty phase result lists required')
    combinations=[]
    for pair in product(*results):
        key={chr(ord(c)+phase*65536):u for phase,row in enumerate(pair)
             for c,u in row['candidate']['key'].items()}
        candidate=Candidate.create('line-table-v1',key=key)
        cost=sum(row['loss']*row['score']['denominator'] for row in pair)
        combinations.append((cost,candidate.id,candidate))
    combinations.sort(key=lambda x:(x[0],x[1]))
    candidates=[x[2] for x in combinations]
    return [candidates[i%len(candidates)] for i in range(width)]
