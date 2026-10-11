import itertools
import unittest

import numpy as np

from voynich.laboratory.word_parts import ProductModel, contrast, folds, splits


class WordPartsTests(unittest.TestCase):
    def test_splits_use_compound_glyphs_and_nonempty_parts(self):
        self.assertEqual(splits('chedy'), (('ch', 'edy'), ('che', 'dy'), ('ched', 'y')))
        self.assertEqual(splits('y'), ())

    def test_product_model_is_normalised_over_its_parts(self):
        model = ProductModel(['qokedy', 'chedy', 'qokaiin', 'chaiin', 'shedy'] * 4)
        self.assertAlmostEqual(sum(model.prefix.values()), 1.0)
        self.assertAlmostEqual(sum(model.suffix.values()), 1.0)
        self.assertEqual(model.probability('zzzz'), 0.0)

    def test_product_text_is_positive_and_chain_text_recovers_structure(self):
        rng = np.random.default_rng(0)
        prefixes = ['qok', 'ch', 'sh', 'ot', 'lk', 'd', 'yt', 'op', 'k', 't', 'ok', 'pch']
        suffixes = ['edy', 'aiin', 'ar', 'ol', 'y', 'eey', 'al', 'dy', 'am', 'or', 'ain', 'eol']
        draw = lambda n: [prefixes[int(rng.integers(12))] + suffixes[int(rng.integers(12))] for _ in range(n)]
        # Hold out a block of combinations entirely, so held-out words are genuinely new types.
        held_types = {p + s for p, s in itertools.product(prefixes[:4], suffixes[:4])}
        words = draw(6000)
        train = [w for w in words if w not in held_types]
        held = [w for w in words if w in held_types]
        result, product, _ = contrast(train, held)
        self.assertEqual(result['new_type_tokens'], result['held_tokens'])
        self.assertEqual(result['coverage_new'], 1.0)
        self.assertGreater(result['T_new'], 0)
        self.assertEqual(product.best_split('qokaiin'), ('qok', 'aiin'))

    def test_folds_alternate_groups(self):
        self.assertEqual(folds(['a', 'a', 'b', 'c', 'c', 'd'], 2), {'a': 0, 'b': 1, 'c': 0, 'd': 1})


if __name__ == '__main__':
    unittest.main()
