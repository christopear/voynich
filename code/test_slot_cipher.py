"""Tests for the syllabic slot cipher (COUPLED_CIPHER_PROTOCOL.md)."""
import unittest
from collections import Counter

import slot_cipher as sc


class FakeTraining:
    """Deterministic core source and a strongly biased edge table."""
    def __init__(self):
        self.k = 0
        self.edge = {("n", "d"): 5.0, ("l", "d"): 0.2, ("n", "k"): 0.2, ("l", "k"): 5.0}

    def fresh(self, rng):
        self.k += 1
        return "d" + "ch" * (self.k % 3) + "e" * (self.k // 3 + 1) + "k"


class SyllableTests(unittest.TestCase):
    def test_syllabify_round_trip(self):
        for w in ("disciplina", "clericalis", "christi", "a", "est", "quia"):
            self.assertEqual("".join(sc.syllabify(w)), w)

    def test_normalization(self):
        self.assertEqual(sc.latin_words("Iam, JUVAT! kalendas W"), ["iam", "iuvat", "calendas", "uu"])


class CodeBookTests(unittest.TestCase):
    def setUp(self):
        self.units = ["a", "di", "re", "tis", "qua"]
        self.book = sc.CodeBook(self.units, FakeTraining(), sc.Config(h=6, s=1.0, beta=0.0), seed=3)

    def test_invertible_and_unique(self):
        words = [self.book.word(u, p, t) for u, opts in self.book.variants.items() for p, t, _ in opts]
        self.assertEqual(len(words), len(set(words)))
        self.assertTrue(all(self.book.decode[self.book.word(u, p, t)] == u
                            for u, opts in self.book.variants.items() for p, t, _ in opts))

    def test_cores_respect_edge_constraints(self):
        for core in self.book.cores.values():
            self.assertFalse(core.startswith(sc.BAD_START))
            self.assertNotIn(core[-1], sc.BAD_END)

    def test_encipher_round_trip_and_determinism(self):
        seq = ["a", "di", "re", "a", "tis", "qua"] * 20
        cfg = sc.Config(h=6, s=1.0, beta=2.0)
        w1 = sc.encipher(seq, self.book, FakeTraining().edge, cfg, seed=9)
        w2 = sc.encipher(seq, self.book, FakeTraining().edge, cfg, seed=9)
        self.assertEqual(w1, w2)
        self.assertEqual([self.book.decode[w] for w in w1], seq)

    def test_coupling_moves_terminal_towards_edge_affinity(self):
        book = sc.CodeBook(["x", "y"], FakeTraining(), sc.Config(h=24, s=0.0, beta=0.0), seed=1)
        seq = ["x", "y"] * 400
        edge = {}
        for u in ("x", "y"):
            edge[("n", book.cores[u][0])] = 5.0; edge[("l", book.cores[u][0])] = 0.2
        free = Counter(w[-1] for w in sc.encipher(seq, book, edge, sc.Config(24, 0.0, 0.0), 5))
        coupled = Counter(w[-1] for w in sc.encipher(seq, book, edge, sc.Config(24, 0.0, 4.0), 5))
        self.assertGreater(coupled["n"] / max(1, coupled["l"]), free["n"] / max(1, free["l"]))


if __name__ == "__main__":
    unittest.main()
