from collections import Counter
import unittest

from voynich.laboratory.codebook_assignment import page_encrypt, ranked_codebook
from voynich.laboratory.structured_codes import RULES
from voynich.laboratory.word_shapes import NGramModel, model_codebook

WORDS = ['daiin', 'chedy', 'qokedy', 'dain', 'chol', 'shedy', 'okaiin', 'qokain', 'dal', 'chey'] * 3
VOCAB = [f'v{i}' for i in range(30)]
FREQ = Counter({w: 100 - i for i, w in enumerate(VOCAB)})


class RankedAssignmentTests(unittest.TestCase):
    def setUp(self):
        self.model = NGramModel(WORDS, 2)
        self.book, _ = ranked_codebook(VOCAB, FREQ, self.model, 3)

    def test_same_strings_as_random_codebook(self):
        base, _ = model_codebook(VOCAB, self.model, 3)
        strings = lambda b: sorted(c for cs in b.encode.values() for c in cs)
        self.assertEqual(strings(base), strings(self.book))

    def test_frequent_words_get_probable_strings(self):
        best = lambda w: max(self.model.logprob(c) for c in self.book.encode[w])
        worst = lambda w: min(self.model.logprob(c) for c in self.book.encode[w])
        ordered = sorted(VOCAB, key=lambda w: -FREQ[w])
        for a, b in zip(ordered, ordered[1:]):
            self.assertGreaterEqual(worst(a), best(b) - 1e-12)

    def test_roundtrip_all_rules(self):
        words = VOCAB * 2
        rows = [dict(page='a' if i < 30 else 'b') for i in range(60)]
        for rule in RULES:
            tokens, _ = page_encrypt(self.book, words, rows, rule, 9)
            self.assertEqual(self.book.decrypt(tokens), words)


if __name__ == '__main__':
    unittest.main()
