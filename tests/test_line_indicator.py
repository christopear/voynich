import unittest

import numpy as np

from voynich.experiments.e35_line_indicator import analyse, plant, position_contributions, shuffle_first_words

GLYPHS = ['d', 'k', 'o', 'q', 's', 't']
ENDS = ['y', 'n', 'l', 'r']


def synthetic(n_pages=12, per_page=30, seed=0):
    rng = np.random.default_rng(seed)
    lines = []
    for p in range(n_pages):
        for i in range(per_page):
            words = [rng.choice(GLYPHS) + 'a' + rng.choice(ENDS, p=[.6, .2, .1, .1]) for _ in range(9)]
            lines.append(dict(page=f'p{p}', folio=f'f{p}', pstart=i == 0, words=words))
    return lines


class LineIndicatorTests(unittest.TestCase):
    def test_targets_skip_the_adjacent_word(self):
        lines = synthetic(2, 20)
        for ln in lines:                      # make word 2's ending copy the key; nothing else depends on it
            ln['words'][1] = ln['words'][1][:-1] + ENDS[GLYPHS.index(ln['words'][0][0]) % 4]
        result = analyse(lines, bootstrap=200)
        self.assertLess(abs(result['excess'][0]), .05)

    def test_null_does_not_fire_and_planted_indicator_does(self):
        fired = sum(analyse(synthetic(seed=s), bootstrap=300)['fires'] for s in range(6))
        self.assertLessEqual(fired, 1)
        lines = synthetic()
        planted = analyse(plant(lines, .6, 1), bootstrap=500)
        self.assertTrue(planted['fires'])
        self.assertGreater(planted['excess'][0], max(planted['excess'][1:]))

    def test_shuffle_keeps_first_word_multiset_per_stratum(self):
        lines = synthetic(3, 10)
        shuffled = shuffle_first_words(lines, 4)
        for page in ('p0', 'p1', 'p2'):
            for flag in (True, False):
                a = sorted(l['words'][0] for l in lines if l['page'] == page and l['pstart'] == flag)
                b = sorted(l['words'][0] for l in shuffled if l['page'] == page and l['pstart'] == flag)
                self.assertEqual(a, b)
        self.assertEqual([l['words'][1:] for l in lines], [l['words'][1:] for l in shuffled])

    def test_contributions_are_deterministic(self):
        lines = synthetic(2, 15)
        a, b = position_contributions(lines, 1, 'final'), position_contributions(lines, 1, 'final')
        self.assertTrue(all(np.allclose(a[p], b[p]) for p in a))


if __name__ == '__main__':
    unittest.main()
