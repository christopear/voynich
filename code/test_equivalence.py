"""Tests for the equivalence-class stage (EQUIVALENCE_PROTOCOL.md)."""
import unittest
from pathlib import Path

import numpy as np

import equivalence as eq
import mechanism_models as mm

DATA = Path(__file__).resolve().parents[1] / "data"


def toy_corpus(min_freq=1):
    return eq.Corpus("toy", [["qokal", "dar", None, "chol"], ["dar", "chol", "qokal"], ["chor", "dar"]], min_freq=min_freq)


class FeatureTests(unittest.TestCase):
    def test_edit_distance(self):
        self.assertEqual(eq.edit_distance(("ch", "o", "l"), ("ch", "o", "r")), 1)
        self.assertEqual(eq.edit_distance((), ("a", "b")), 2)

    def test_form_features_symmetric(self):
        a, b = ("o", "k", "a", "l"), ("o", "t", "a", "r")
        self.assertEqual(eq.form_features(a, b), eq.form_features(b, a))

    def test_terminal_alternation(self):
        names = eq.FEATURE_GROUPS["form"]
        f = dict(zip(names, eq.form_features(("ch", "o", "l"), ("ch", "o", "r"))))
        self.assertTrue(f["terminal_alternation"])
        f = dict(zip(names, eq.form_features(("ch", "o", "l"), ("ch", "o", "l", "y"))))
        self.assertFalse(f["terminal_alternation"])

    def test_missing_readings_are_not_bridged(self):
        c = toy_corpus()
        i = c.types.index("dar")
        right = dict(zip([*[w for w, _ in c.freq.most_common(eq.TOP_CONTEXT)], "^", "$", "*"], c.R[i]))
        # 'dar' precedes None on line 1: that occurrence contributes no right context.
        self.assertEqual(right["chol"], 1)
        self.assertEqual(right["$"], 1)
        self.assertEqual(c.R[i].sum(), 2)

    def test_feature_matrix_shape_and_no_label_features(self):
        c = toy_corpus()
        X, names = c.feature_matrix()
        self.assertEqual(X.shape, (len(c.pairs()), len(names)))
        self.assertFalse(any("label" in n or "plain" in n for n in names))
        self.assertEqual(eq.features_of(), [n for g in eq.PRIMARY_GROUPS for n in eq.FEATURE_GROUPS[g]])


class ValidationTests(unittest.TestCase):
    def test_grouped_cv_never_trains_on_test_types(self):
        types = [f"t{k}" for k in range(20)]
        pairs = [(i, j) for i in range(20) for j in range(i + 1, 20)]
        folds = eq.assign_folds(types)
        for f in range(5):
            train = {t for i, j in pairs for t in (i, j) if folds[types[i]] != f and folds[types[j]] != f}
            test = {t for i, j in pairs for t in (i, j) if folds[types[i]] == f and folds[types[j]] == f}
            self.assertFalse(train & test)

    def test_assign_folds_deterministic(self):
        self.assertEqual(eq.assign_folds(list("abcdefg")), eq.assign_folds(list("gfedcba")))

    def test_cluster_threshold(self):
        labels = eq.cluster(3, [(0, 1), (0, 2), (1, 2)], np.array([0.9, 0.1, 0.1]))
        self.assertEqual(labels[0], labels[1]); self.assertNotEqual(labels[0], labels[2])

    def test_cluster_scores_perfect(self):
        s = eq.cluster_scores(["a", "a", "b"], [1, 1, 2])
        self.assertEqual((s["pair_precision"], s["pair_recall"], s["ari"]), (1.0, 1.0, 1.0))


@unittest.skipUnless((DATA / "mechanisms/naibbe_tables.csv").exists(), "Naibbe tables not present")
class TransferTargetTests(unittest.TestCase):
    def test_encoded_labels_come_from_exact_decoding(self):
        enc = mm.Encoder(DATA / "mechanisms/naibbe_tables.csv")
        words, audit = mm.generate(None, enc, mm.clean_plain("arma virumque cano " * 50), 200,
                                   dict(mechanism="encoding", level=1, coupling=0), eq.SEED)
        self.assertTrue(audit["roundtrip"])
        self.assertTrue(all(w in enc.reverse for w in words))


if __name__ == "__main__":
    unittest.main()
