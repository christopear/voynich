import itertools
import math
import unittest

import numpy as np

from voynich.experiments.e29_frequency_currier_a import decomposition
from voynich.laboratory.structured_codes import RULES
from voynich.laboratory.word_shapes import (
    END, MAX_GLYPHS, START, UNK, NGramModel, coupling_records, model_codebook, stratified_decomposition,
)

WORDS = ['daiin', 'chedy', 'qokedy', 'dain', 'chol', 'shedy', 'okaiin', 'qokain', 'dal', 'chey'] * 3


def rows_for(n, pages=4):
    per = n // pages
    return [dict(page=f'p{i//per}', section='H' if i < n//2 else 'B', roles=(i % 8 == 0, i % 8 == 7, i % per < 8),
                 locus=f'p{i//per}.{(i % per)//8}', start=i % 8, end=i % 8) for i in range(n)]


class WordShapeTests(unittest.TestCase):
    def test_witten_bell_distributions_normalise(self):
        for order in (1, 2, 3):
            model = NGramModel(WORDS, order)
            contexts = [k for k in model.counts] + [(START,)*order, ('x', 'y', 'z')[:order], ('d', UNK, 'a')[:order]]
            for context in contexts:
                p = model.distribution(list(context))
                self.assertAlmostEqual(float(p.sum()), 1.0, places=12)
                self.assertTrue(np.all(p > 0))

    def test_top_matches_brute_force(self):
        model = NGramModel(['ab', 'ba', 'aab', 'b'], 1)
        letters = [g for g in model.alphabet if g not in (END, UNK)]
        brute = []
        for n in range(1, 5):
            for glyphs in itertools.product(letters, repeat=n):
                brute.append((''.join(glyphs), model.logprob(''.join(glyphs))))
        brute.sort(key=lambda kv: -kv[1])
        top = model.top(12)
        self.assertEqual(len(top), 12)
        # Probabilities agree with direct scoring and are the 12 largest (ties allowed).
        for word, logp in top:
            self.assertAlmostEqual(logp, model.logprob(word))
        self.assertAlmostEqual(top[-1][1], brute[11][1])
        self.assertTrue(all(len(w) <= MAX_GLYPHS for w, _ in model.top(50)))

    def test_logprob_sums_to_one_over_short_words(self):
        model = NGramModel(['ab', 'ba'], 1)
        letters = [g for g in model.alphabet if g not in (END, UNK)]
        total = sum(2**model.logprob(''.join(g)) for n in range(1, 9) for g in itertools.product(letters, repeat=n))
        self.assertLess(total, 1.0)
        self.assertGreater(total, 0.5)

    def test_stratified_decomposition_reproduces_stage_29(self):
        rng = np.random.default_rng(4)
        rows = rows_for(256)
        tokens = [f'w{x}' for x in rng.integers(40, size=256)]
        self.assertEqual(decomposition(tokens, rows),
                         stratified_decomposition(tokens, rows, [r['section'] for r in rows]))
        self.assertEqual(decomposition(tokens, rows, 'roles'),
                         stratified_decomposition(tokens, rows, [(r['section'], tuple(r['roles'])) for r in rows]))
        same = stratified_decomposition(tokens, rows, [(r['section'], '1') for r in rows])
        self.assertEqual(same, decomposition(tokens, rows))

    def test_coupling_respects_lines_and_hard_gaps(self):
        rows = [dict(page='p', locus='p.1', start=0, end=0), dict(page='p', locus='p.1', start=1, end=1),
                dict(page='p', locus='p.1', start=3, end=3), dict(page='p', locus='p.2', start=0, end=0)]
        tokens = ['dain', 'chol', 'dar', 'qol']
        records = coupling_records(tokens, rows)
        # dain->chol is adjacent; chol->dar crosses a hard gap; dar->qol crosses a line.
        self.assertEqual(records, [('n', 'ch', 'p')])

    def test_model_codebook_distinct_and_roundtrips(self):
        model = NGramModel(WORDS, 2)
        vocabulary = [f'v{i}' for i in range(40)]
        book, draws = model_codebook(vocabulary, model, 5)
        codes = [c for cs in book.encode.values() for c in cs]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertGreaterEqual(draws, 80)
        self.assertEqual(book.encode, model_codebook(vocabulary, model, 5)[0].encode)
        words = vocabulary * 3
        pages = ['a'] * 60 + ['b'] * 60
        for rule in RULES:
            tokens, _ = book.encrypt(words, pages, rule, 11)
            self.assertEqual(book.decrypt(tokens), words)

    def test_samples_are_bounded(self):
        model = NGramModel(WORDS, 3)
        rng = np.random.default_rng(1)
        lengths = [len(model.sample(rng)) for _ in range(200)]
        self.assertTrue(min(lengths) >= 1)
        self.assertFalse(math.isnan(model.cross_entropy(['daiin', 'xyz'])))


if __name__ == '__main__':
    unittest.main()
