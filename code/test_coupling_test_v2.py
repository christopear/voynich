"""Tests for coupling_test_v2 (COUPLING_TEST_V2_PROTOCOL.md)."""
import random
import unittest

import numpy as np

import coupling_test_v2 as v2
from test_coupling_test import synthetic


def toy_lines(seed=0, n=300):
    rng = random.Random(seed)
    # Two "homophone" spellings (xa, xb) share contexts; y is used elsewhere.
    lines = []
    for _ in range(n):
        lines.append([rng.choice(["pa", "pb"]), rng.choice(["xa", "xb"]), "qq",
                      rng.choice(["ra", "rb"]), "y", "zz"])
    return lines


class ClassTests(unittest.TestCase):
    def test_neighbour_classes_deterministic_and_group_homophones(self):
        lines = toy_lines()
        c1 = v2.neighbour_classes(lines, k=4, dim=4, top_ctx=50)
        c2 = v2.neighbour_classes(lines, k=4, dim=4, top_ctx=50)
        self.assertEqual(c1, c2)
        self.assertEqual(c1["xa"], c1["xb"])      # same contexts -> same class
        self.assertEqual(c1["pa"], c1["pb"])

    def test_records_mapping(self):
        occ = v2.Occurrences([["a", "b", "c"], ["b", None, "d"]])
        recs = occ.records("b", {"a": "c1"}, "rare")
        self.assertEqual(recs, [("a", "c", "c", "c1", "rare")])   # second 'b' is next to a gap

    def test_identity_map(self):
        m = v2.identity_map([["a", "a", "b"]], top=1)
        self.assertEqual(m, {"a": "a"})


class PooledTests(unittest.TestCase):
    def test_pooled_size_and_power(self):
        null_res = [v2.residual_test(*synthetic(False, n=300, seed=s), reps=100) for s in range(12)]
        alt_res = [v2.residual_test(*synthetic(True, n=300, seed=s), reps=100) for s in range(12)]
        self.assertGreater(v2.pooled(null_res)["p"], 0.05)
        self.assertLess(v2.pooled(alt_res)["p"], 0.05)
        self.assertEqual(len(null_res[0]["null_z"]), 100)
        self.assertAlmostEqual(float(np.mean(null_res[0]["null_z"])), 0.0, places=5)


if __name__ == "__main__":
    unittest.main()
