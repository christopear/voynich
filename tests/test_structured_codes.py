import math
from collections import Counter
import unittest

from voynich.laboratory.structured_codes import (
    RULES, SlotGrammar, WordCodebook, control_indices, glyph_profile,
)


class StructuredCodeTests(unittest.TestCase):
    def setUp(self):
        self.book = WordCodebook({'a': ['ax', 'ay'], 'b': ['bx', 'by']})

    def test_collisions_are_counted_not_extra_capacity(self):
        grammar = SlotGrammar.from_slots([
            [(('a',), 1), (('a', 'b'), 1)],
            [((), 1), (('b',), 1)], [(('c',), 1)]])
        self.assertEqual(grammar.combinations, 4)
        self.assertEqual(len(grammar.weights), 3)
        self.assertEqual(grammar.weights['abc'], 2)
        with self.assertRaises(ValueError):
            WordCodebook.make(['a', 'b'], grammar, 1)

    def test_reject_ambiguous_dictionary(self):
        with self.assertRaises(ValueError):
            WordCodebook({'a': ['x', 'y'], 'b': ['y', 'z']})

    def test_roundtrips_replay_and_probability_cost(self):
        words = ['a', 'b', 'a', 'b']*4
        pages = ['p1']*8+['p2']*8
        for rule in RULES:
            tokens, audit = self.book.encrypt(words, pages, rule, 37)
            self.assertEqual(self.book.decrypt(tokens), words)
            self.assertEqual((tokens, audit), self.book.encrypt(words, pages, rule, 37))
            expected = audit['fair_bit_draws'] - sum(math.log2(.25 if yes else .75)
                                                    for _, yes in audit['refresh_events'])
            self.assertAlmostEqual(audit['trajectory_bits'], expected)
            if rule == 'iid':
                self.assertEqual(audit['fair_bit_draws'], 16)
            if rule == 'page':
                self.assertEqual(audit['fair_bit_draws'], 2)
                self.assertEqual(len(set(audit['choices'][:8])), 1)
            if rule == 'word_page':
                self.assertEqual(audit['fair_bit_draws'], 4)
                self.assertEqual(audit['peak_variant_state_bits'], 2)
                self.assertEqual(tokens[0], tokens[2])
                self.assertEqual(tokens[1], tokens[3])

    def test_controls_preserve_page_role_margins_and_line_chunks(self):
        rows = []
        for p in range(2):
            for line, length in enumerate((3, 4, 5, 3)):
                for i in range(length):
                    rows.append(dict(page=p, locus=f'{p}.{line}', roles=(i == 0, i == length-1, line < 2)))
        for kind in ('word', 'line'):
            order = control_indices(rows, kind, 13)
            self.assertEqual(sorted(order), list(range(len(rows))))
            new = [rows[i] for i in order]
            self.assertEqual(Counter((r['page'], r['roles']) for r in new),
                             Counter((r['page'], r['roles']) for r in rows))
            self.assertEqual([r['page'] for r in new], [r['page'] for r in rows])
            if kind == 'line':
                for locus in {r['locus'] for r in rows}:
                    ix = [i for i in order if rows[i]['locus'] == locus]
                    self.assertEqual(ix, sorted(ix))
                    positions = [i for i, r in enumerate(new) if r['locus'] == locus]
                    self.assertEqual(positions, list(range(min(positions), max(positions)+1)))

    def test_glyph_entropy_has_known_value(self):
        self.assertAlmostEqual(glyph_profile(['ab', 'ac'])['conditional_entropy'], 1)
        self.assertAlmostEqual(glyph_profile(['ab', 'ab'])['conditional_entropy'], 0)


if __name__ == '__main__':
    unittest.main()
