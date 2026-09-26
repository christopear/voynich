"""Tests for coupling_test_v3 (COUPLING_TEST_V3_PROTOCOL.md)."""
import random
import unittest
from collections import Counter

import coupling_test_v3 as v3


def paged_corpus(n_pages=10, lines_per_page=30, seed=0):
    rng = random.Random(seed)
    out = []
    for p in range(n_pages):
        for _ in range(lines_per_page):
            out.append((f"f{p}r", [rng.choice(["pa", "pb"]), rng.choice(["xa", "xb"]), "qq",
                                   rng.choice(["ra", "rb"]), "y", "zz"]))
    return out


class FoldTests(unittest.TestCase):
    def test_page_folds_deterministic_and_balanced(self):
        pages = [f"f{i}" for i in range(23)]
        f1 = v3.page_folds(pages); f2 = v3.page_folds(list(reversed(pages)))
        self.assertEqual(f1, f2)
        self.assertEqual(set(f1), set(pages))
        sizes = Counter(f1.values())
        self.assertLessEqual(max(sizes.values()) - min(sizes.values()), 1)

    def test_cross_fitting_hides_a_folds_own_neighbours(self):
        corpus = paged_corpus()
        folds = v3.page_folds([p for p, _ in corpus])
        page0 = sorted(folds)[0]
        # A neighbour word that occurs ONLY on page0, next to "xa".
        corpus.append((page0, ["uniq", "xa", "qq"]))
        corpus.append((page0, ["uniq", "xa", "qq"]))
        occ = v3.CrossFitOccurrences(corpus, "k4", folds)
        # For occurrences on page0's fold, 'uniq' was never seen in the training folds -> 'rare'.
        mapped = [rec[3] for raw, rec in zip(occ.raw["xa"], occ.records("xa"))
                  if raw[5] == folds[page0] and raw[3] == "uniq"]
        self.assertEqual(mapped, ["rare", "rare"])

    def test_identity_arm_is_fold_independent(self):
        corpus = paged_corpus()
        occ = v3.CrossFitOccurrences(corpus, "top30")
        self.assertEqual(len({id(m) for m in occ.maps.values()}), 1)
        self.assertEqual(occ.default, "*")

    def test_records_accept_v2_call_signature(self):
        occ = v3.CrossFitOccurrences(paged_corpus(), "top30")
        self.assertEqual(occ.records("xa"), occ.records("xa", None, None))


class SubsetTests(unittest.TestCase):
    def test_disjoint_subsets(self):
        rows = [{"seed": s, "a": f"w{s}_{i}", "b": f"w{s}_{i + 1}"} for s in (1, 2) for i in range(80)]
        subs = v3.disjoint_subsets(rows, 20, 15)
        self.assertEqual(len(subs), 15)
        for sub in subs:
            self.assertEqual(len(sub), 20)
            self.assertEqual(len({r["seed"] for r in sub}), 1)
            members = [m for r in sub for m in (r["a"], r["b"])]
            self.assertEqual(len(members), len(set(members)))


if __name__ == "__main__":
    unittest.main()
