import unittest

import numpy as np

from voynich.experiments.e36_label_units import (
    decomposable, frequency_bin, load, permute_within_kind, split_hits, splits, whole_hits,
)


class LabelUnitTests(unittest.TestCase):
    def test_splits_use_compound_glyphs(self):
        self.assertEqual(splits('chol'), (('ch', 'ol'), ('cho', 'l')))
        self.assertTrue(decomposable('otaldy', {'ot', 'aldy'}))
        self.assertFalse(decomposable('otaldy', {'ot', 'ldy'}))

    def test_frequency_bins(self):
        self.assertEqual([frequency_bin(c) for c in (0, 1, 2, 4, 5, 19, 20)], [0, 1, 2, 2, 3, 3, 4])

    def test_hits_are_page_local(self):
        labels = [dict(page='a', kind='Lz', word='otaldy'), dict(page='b', kind='Lz', word='otaldy')]
        self.assertEqual(whole_hits(labels, {'a': {'otaldy'}}).tolist(), [1., 0.])
        self.assertEqual(split_hits(labels, {'b': {('ot', 'aldy')}}).tolist(), [0., 1.])

    def test_permutation_keeps_kinds_and_word_multiset(self):
        labels = [dict(page=f'p{i}', kind='Lz' if i % 2 else 'Lf', word=f'w{i}') for i in range(20)]
        out = permute_within_kind(labels, np.random.default_rng(1))
        self.assertEqual([l['page'] for l in out], [l['page'] for l in labels])
        for kind in ('Lz', 'Lf'):
            self.assertEqual(sorted(l['word'] for l in out if l['kind'] == kind),
                             sorted(l['word'] for l in labels if l['kind'] == kind))

    def test_real_data_excludes_sealed_pages_and_respects_drawing_gaps(self):
        data = load()
        self.assertEqual(len(data['labels']), 778)
        self.assertNotIn('f20r', data['words'])          # a sealed confirmation page
        # f1r line 1 has ordinary gaps: fachys.ykal is a neighbour pair.
        self.assertIn(('fachys', 'ykal'), data['pairs']['f1r'])


if __name__ == '__main__':
    unittest.main()
