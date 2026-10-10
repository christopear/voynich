from collections import Counter
import unittest

from voynich.experiments.e06_boundary_frontier import parse_body
from voynich.experiments.e37_ending_markers import analyse, ending_table, glyphs, m1, stem, stream
from voynich.voynich_core import eva_glyphs


def line(body, page='p1'):
    words, gaps = parse_body(body)
    return dict(page=page, words=words, gaps=gaps)


class EndingMarkerTests(unittest.TestCase):
    def test_glyphs_match_core_tokeniser_and_stem(self):
        for word in ('chedy', 'qokaiin', 'shol', 'cthor', 'daiin'):
            self.assertEqual(list(glyphs(word)), eva_glyphs(word))
        self.assertEqual(stem('chol'), 'cho')
        self.assertEqual(stem('otch'), 'ot')

    def test_stream_respects_real_drawing_gap(self):
        tokens = stream([line('dain.chol<->dar,shedy')])
        self.assertEqual([t['next'] for t in tokens], ['ch', None, 'sh', None])

    def test_common_share_counts_stems(self):
        tokens = stream([line('.'.join(['da'] * 5 + ['dan'] * 4 + ['chey'] * 3))])
        counts = Counter(t['word'] for t in tokens)
        table = ending_table(tokens, counts, minimum=1)
        self.assertEqual(table['n']['common'], 1.0)      # stem 'da' occurs five times
        self.assertEqual(table['y']['attested'], 0.0)    # stem 'che' never occurs
        result = m1(tokens, counts, ('n',), bootstrap=50)
        self.assertEqual(result['D'], 1.0)

    def test_marker_fires_and_lexical_ending_does_not(self):
        import numpy as np
        rng = np.random.default_rng(0)
        stems = ['da', 'cho', 'she', 'oka', 'qo', 'ota', 'che', 'dy']
        marker, lexical = [], []
        for p in range(30):
            words = [stems[int(i)] for i in rng.integers(len(stems), size=120)]
            marked = [w + ('z' if (nxt[0] in 'dco') == (rng.random() < .9) else '') for w, nxt in zip(words, words[1:] + ['da'])]
            marker.append(line('.'.join(marked), f'p{p}'))
            lexical.append(line('.'.join(w + 'z' if w in ('da', 'cho') else w for w in words), f'p{p}'))
        self.assertTrue(analyse(stream(marker), ('z',))['fires'])
        self.assertFalse(analyse(stream(lexical), ('z',))['fires'])


if __name__ == '__main__':
    unittest.main()
