import unittest

from voynich.experiments.e27_unit_association import association
from voynich.experiments.e29_frequency_currier_a import decomposition, extract_pages


class FrequencyAssociationTests(unittest.TestCase):
    def test_additivity_with_unequal_roles_and_all_frequency_bins(self):
        tokens = ['a', 'a', 'a', 'b', 'b', 'c', 'd', 'a', 'a', 'e', 'f', 'f']
        rows = [dict(page=str(i//4), section='H', roles=(i % 3 == 0, False, False))
                for i in range(len(tokens))]
        for condition in ('section', 'roles'):
            actual = decomposition(tokens, rows, condition, permutations=29)
            expected = association(tokens, rows, condition, permutations=29, seed=2901)
            for key in ('raw', 'null_mean', 'excess'):
                self.assertAlmostEqual(actual['total'][key], expected[key], places=12)
                self.assertAlmostEqual(sum(x[key] for x in actual['bins'].values()), expected[key], places=12)
            self.assertAlmostEqual(sum(x['token_mass'] for x in actual['bins'].values()), 1)

    def test_unique_words_cannot_manufacture_page_association(self):
        tokens = [str(i) for i in range(64)]
        rows = [dict(page=str(i//8), section='H') for i in range(64)]
        actual = decomposition(tokens, rows, permutations=19)
        self.assertAlmostEqual(actual['total']['excess'], 0, places=12)

    def test_planted_repeated_rare_words(self):
        tokens = [f'{i//16}_{i%4}' for i in range(128)]
        rows = [dict(page=str(i//16), section='H') for i in range(128)]
        actual = decomposition(tokens, rows, permutations=29)
        self.assertGreater(actual['bins']['count2to4']['excess'], .5)
        self.assertEqual(actual['bins']['count5plus']['excess'], 0)

    def test_extractor_keeps_classification_and_respects_hard_gaps(self):
        line = dict(page='f1r', folio='f1', locus='f1r.1', paragraph_start=True,
                    words=[dict(word=w, clean=True) for w in ('a', 'b', 'c', 'd')],
                    gaps=['uncertain', 'drawing', 'ordinary'])
        rows = extract_pages([line], {'f1r': 'A'}, join=True)['f1r']
        self.assertEqual([r['word'] for r in rows], ['ab', 'c', 'd'])
        self.assertTrue(all(r['currier'] == 'A' for r in rows))
        self.assertEqual((rows[0]['start'], rows[0]['end']), (0, 1))
        self.assertEqual(extract_pages([line], {}), {})


if __name__ == '__main__':
    unittest.main()
