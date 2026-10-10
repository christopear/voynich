import math
import unittest

from voynich.laboratory.context_choice import CONTEXT_RULES, make_encrypt, successors
from voynich.laboratory.structured_codes import WordCodebook

BOOK = WordCodebook({'a': ['dain', 'day'], 'b': ['chol', 'qol'], 'c': ['ror', 'roy']})
LIFT = {('n', 'ch'): 4., ('y', 'ch'): .25, ('n', 'q'): .25, ('y', 'q'): 4.}


def rows(n, gap_after=None, line_break=None):
    out, line, pos = [], 0, 0
    for i in range(n):
        out.append(dict(page='p', locus=f'p.{line}', start=pos, end=pos))
        pos += 2 if gap_after == i else 1
        if line_break == i:
            line, pos = line + 1, 0
    return out


class ContextChoiceTests(unittest.TestCase):
    def test_successors_respect_lines_and_gaps(self):
        r = rows(5, gap_after=1, line_break=2)
        self.assertEqual(successors(r), [1, None, None, 4, None])

    def test_edge_max_follows_encoded_successor(self):
        encrypt = make_encrypt(LIFT)
        # 'b' is last (no context, fair bit); 'a' must then suit b's chosen codeword.
        for seed in range(20):
            tokens, audit = encrypt(BOOK, ['a', 'b'], rows(2), 'edge_max', seed)
            self.assertEqual(tokens[0], 'dain' if tokens[1].startswith('ch') else 'day')
            self.assertEqual(BOOK.decrypt(tokens), ['a', 'b'])
            self.assertEqual(audit['informative_choices'], 1)

    def test_no_context_across_hard_gap(self):
        encrypt = make_encrypt(LIFT)
        _, audit = encrypt(BOOK, ['a', 'b'], rows(2, gap_after=0), 'edge_max', 1)
        self.assertEqual(audit['context_choices'], 0)

    def test_iid_matches_page_rule_and_all_roundtrip(self):
        encrypt = make_encrypt(LIFT)
        words = ['a', 'b', 'c', 'a', 'b', 'c', 'a', 'a'] * 4
        r = rows(len(words), line_break=7)
        self.assertEqual(encrypt(BOOK, words, r, 'iid', 5), BOOK.encrypt(words, ['p']*len(words), 'iid', 5))
        for rule in CONTEXT_RULES:
            tokens, audit = encrypt(BOOK, words, r, rule, 5)
            self.assertEqual(BOOK.decrypt(tokens), words)
            self.assertEqual((tokens, audit), encrypt(BOOK, words, r, rule, 5))

    def test_edge_trajectory_cost(self):
        encrypt = make_encrypt(LIFT)
        tokens, audit = encrypt(BOOK, ['a', 'b'], rows(2), 'edge', 3)
        p = 4/(4+.25)
        chosen = p if (tokens[0] == 'dain') == tokens[1].startswith('ch') else 1-p
        self.assertAlmostEqual(audit['trajectory_bits'], 1 - math.log2(chosen))


if __name__ == '__main__':
    unittest.main()
