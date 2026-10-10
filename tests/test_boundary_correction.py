import json
import unittest

from voynich.experiments.e06_boundary_frontier import load_lines, parse_body
from voynich.experiments.e29_frequency_currier_a import extract_pages
from voynich.laboratory.boundary_correction import (
    annotate, canonical_top, coupling_records, make_context_encrypt, neighbours,
)
from voynich.laboratory.structured_codes import WordCodebook
from voynich.laboratory.word_shapes import NGramModel, coupling_records as old_records
from voynich.paths import ROOT


def line(body, locus='f1.1'):
    words, gaps = parse_body(body)
    return dict(page='f1', folio='f1', locus=locus, paragraph_start=False, words=words, gaps=gaps, meta={})


class BoundaryCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.line = line('dain.chol<->dar.qokain,shedy.dal')
        self.rows = [r for rows in extract_pages([self.line], {'f1': 'B'}).values() for r in rows]
        self.rows = annotate(self.rows, {'f1.1': self.line})

    def test_real_drawing_gap_is_not_a_neighbour(self):
        self.assertEqual(self.line['gaps'], ['ordinary', 'drawing', 'ordinary', 'uncertain', 'ordinary'])
        # Indices are consecutive across the drawing, which is what fooled the old rule.
        self.assertEqual([r['start'] for r in self.rows], [0, 1, 2, 3, 4, 5])
        self.assertEqual(neighbours(self.rows), [1, None, 3, 4, 5, None])
        tokens = [r['word'] for r in self.rows]
        self.assertIn(('l', 'd', 'f1'), old_records(tokens, self.rows))      # old rule crosses the drawing
        self.assertNotIn(('l', 'd', 'f1'), coupling_records(tokens, self.rows))
        self.assertIn(('n', 'ch', 'f1'), coupling_records(tokens, self.rows))
        self.assertIn(('n', 'sh', 'f1'), coupling_records(tokens, self.rows))  # uncertain space counts

    def test_joined_tokens_use_gap_after_their_last_word(self):
        rows = [r for rs in extract_pages([self.line], {'f1': 'B'}, join=True).values() for r in rs]
        rows = annotate(rows, {'f1.1': self.line})
        self.assertEqual([r['word'] for r in rows], ['dain', 'chol', 'dar', 'qokainshedy', 'dal'])
        self.assertEqual(neighbours(rows), [1, None, 3, 4, None])

    def test_manuscript_development_panel_drops_drawing_pairs(self):
        slots = json.loads((ROOT/'results/frequency_currier_a_2026-10-09/slots.json').read_text())
        lines = {ln['locus']: ln for ln in load_lines(ROOT/'data/ZL3b-n.txt')}
        rows = annotate(slots['B_ZL_split_early'], lines)
        drawing = sum(r['gap_after'] == 'drawing' for r in rows)
        self.assertGreater(drawing, 0)
        tokens = [r['word'] for r in rows]
        self.assertEqual(len(old_records(tokens, rows)) - len(coupling_records(tokens, rows)), 10)

    def test_context_choice_ignores_drawing_successor(self):
        book = WordCodebook({'a': ['dain', 'day'], 'b': ['chol', 'qol']})
        encrypt = make_context_encrypt({('n', 'ch'): 4., ('y', 'ch'): .25, ('n', 'q'): .25, ('y', 'q'): 4.})
        l = line('x<->y')
        rows = annotate([dict(page='f1', locus='f1.1', start=0, end=0), dict(page='f1', locus='f1.1', start=1, end=1)],
                        {'f1.1': l})
        tokens, audit = encrypt(book, ['a', 'b'], rows, 'edge_max', 3)
        self.assertEqual(audit['context_choices'], 0)
        self.assertEqual(book.decrypt(tokens), ['a', 'b'])

    def test_canonical_top_is_distinct(self):
        model = NGramModel(['ch', 'c', 'h', 'chh', 'hc', 'cch'] * 3, 1)
        listed = [w for w, _ in model.top(20)]
        fixed = [w for w, _ in canonical_top(model, 20)]
        self.assertLess(len(set(listed)), len(listed))
        self.assertEqual(len(set(fixed)), len(fixed))
        self.assertEqual(len(fixed), 20)


if __name__ == '__main__':
    unittest.main()
