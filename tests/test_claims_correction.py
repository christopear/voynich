import unittest

import numpy as np

from voynich.experiments.posthoc_e35_claims_correction import m2_by_page, naibbe_tables, permute_endings, simulate_naibbe
from voynich.experiments.e37_ending_markers import m2


class ClaimsCorrectionTests(unittest.TestCase):
    def test_simulation_uses_table_entries_and_is_deterministic(self):
        tables = naibbe_tables()
        letters = list('aeinrst' * 200)
        a = simulate_naibbe(letters, ['alpha'], False, 300, 1)
        self.assertEqual(a, simulate_naibbe(letters, ['alpha'], False, 300, 1))
        unigrams = set(tables['alpha']['unigram'].values())
        pairs = {p + s for p in tables['alpha']['prefix'].values() for s in tables['alpha']['suffix'].values()}
        self.assertTrue(all(w in unigrams or w in pairs for w in a))

    def test_permuted_endings_keep_each_lines_ending_multiset(self):
        lines = [dict(page='p', pstart=False, folio='f', words=['tar' if i % 2 else 'dar', 'dain', 'chol', 'shedy', 'qokal', 'dar', 'oky', 'chey', 'sal'])
                 for i in range(40)]
        out, share = permute_endings(lines, 3)
        self.assertGreater(share, 0)
        for before, after in zip(lines, out):
            self.assertEqual(sorted(w[-1] for w in before['words'][1:]), sorted(w[-1] for w in after['words'][1:]))

    def test_page_conditioning_removes_a_pure_page_confound(self):
        rng = np.random.default_rng(0)
        tokens = []
        for p in range(40):
            high = p % 2 == 0                        # high pages: mostly marked forms AND mostly initial 'd'
            for _ in range(60):
                word = 'da' + ('z' if rng.random() < (.8 if high else .1) else '')
                tokens.append(dict(page=f'p{p}', word=word, next='d' if rng.random() < (.8 if high else .2) else 'k'))
        self.assertLess(m2(tokens, ('z',), permutations=199)['p'], .0125)          # pooled test is fooled
        self.assertGreater(m2_by_page(tokens, ('z',), permutations=199)['p'], .0125)


if __name__ == '__main__':
    unittest.main()
