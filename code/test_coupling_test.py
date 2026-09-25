"""Tests for the coupling-aware terminal-alternation statistic."""
import random
import unittest

import numpy as np

import coupling_test as ct
import slot_cipher as sc
from test_slot_cipher import FakeTraining


def synthetic(dep_on_word: bool, n=600, seed=0):
    """Records (prev_final, next_initial, next2, X_left, X_right) for A and B."""
    rng = random.Random(seed)
    a, b = [], []
    for _ in range(n):
        z_next = rng.choice("dkso")
        x_right = rng.choice(["w1", "w2", "w3", "w4"])
        # Choice depends on Z only (coupled homophony) or on the next word itself.
        if dep_on_word:
            pick_a = rng.random() < (0.8 if x_right in ("w1", "w2") else 0.2)
        else:
            pick_a = rng.random() < (0.8 if z_next in "dk" else 0.2)
        rec = (rng.choice("yn"), z_next, z_next + "e", rng.choice(["v1", "v2"]), x_right)
        (a if pick_a else b).append(rec)
    return a, b


class StatisticTests(unittest.TestCase):
    def test_permutation_preserves_strata(self):
        rng = np.random.default_rng(1)
        t = np.array([0, 1, 1, 0, 1, 0, 0, 1]); z = np.array([0, 0, 1, 1, 1, 2, 2, 2])
        for _ in range(20):
            p = ct._permute_within(t, z, rng)
            for g in set(z):
                self.assertEqual(sorted(p[z == g]), sorted(t[z == g]))

    def test_cmi_zero_when_independent_within_strata(self):
        t = np.array([0, 1, 0, 1]); x = np.array([0, 0, 1, 1]); z = np.zeros(4, dtype=int)
        self.assertAlmostEqual(ct._cmi(t, x, z, 2, 1), 0.0)

    def test_z_only_dependence_is_not_flagged(self):
        a, b = synthetic(dep_on_word=False)
        self.assertGreater(ct.residual_test(a, b, reps=200)["p"], 0.05)
        self.assertLess(ct.naive_test(a, b, reps=200)["p"], 0.05)   # the naive test is fooled

    def test_word_dependence_is_flagged(self):
        a, b = synthetic(dep_on_word=True)
        self.assertLess(ct.residual_test(a, b, reps=200)["p"], 0.05)

    def test_stem_final_and_pairs(self):
        self.assertEqual(ct.stem_final("chol"), ("cho", "l"))
        self.assertEqual(ct.stem_final("ch"), (None, None))
        occ = ct.Occurrences([["chol", "dar", "chor"] * 10, ["chor", "dal", "chol"] * 10])
        self.assertIn(("chol", "chor"), ct.same_stem_pairs(occ, set("lr"), min_occ=5))


class SharedCoreTests(unittest.TestCase):
    def test_shared_core_codebook(self):
        counts = {"a": 50, "di": 40, "re": 30, "tis": 20, "qua": 10}
        book = sc.SharedCoreCodeBook(counts, FakeTraining(), sc.Config(10, 1.0, 0.0), seed=4)
        self.assertEqual(book.cores["a"], book.cores["di"])       # adjacent-rank pair shares a core
        self.assertEqual(book.cores["re"], book.cores["tis"])
        ta = {t for _, t, _ in book.variants["a"]}; td = {t for _, t, _ in book.variants["di"]}
        self.assertFalse(ta & td)                                    # disjoint terminals
        words = [book.word(u, p, t) for u, o in book.variants.items() for p, t, _ in o]
        self.assertEqual(len(words), len(set(words)))
        seq = ["a", "di", "re", "tis", "qua"] * 30
        self.assertEqual([book.decode[w] for w in sc.encipher(seq, book, {}, sc.Config(10, 1.0, 2.0), 3)], seq)


if __name__ == "__main__":
    unittest.main()
