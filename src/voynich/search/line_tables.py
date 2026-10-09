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
    if period not in (1, 2):
        raise ValueError('only one or two line tables are implemented')
    if not lines or not any(line.strip() for line in lines):
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
        score = ScoreReport('line-table-v1', (('language_bits', model(self.training,4).nll(plain)),
                            ('table_bits', self.key_cost), ('period_bits', 1.)), self.denominator)
        return Evaluation(score, {'plaintext': plain})


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
