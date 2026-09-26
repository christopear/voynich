"""Checks for the cipher-family generators and fingerprints."""
import random
import unittest

import cipher_families as cf


class FamilyTests(unittest.TestCase):
    def test_homophone_table_uses_exactly_k_symbols(self):
        words = cf.plain_words("latin")
        for k in (40, 60, 90):
            table = cf.homophone_table(words, k)
            self.assertEqual(sum(len(v) for v in table.values()), k)
            self.assertEqual(len({s for v in table.values() for s in v}), k)

    def test_abbreviation_contracts_affixes(self):
        rng = random.Random(1)
        self.assertEqual(cf.abbreviate("dominus", 0.0, rng), "domin[us]")
        self.assertTrue(cf.abbreviate("confessionibus", 0.0, rng).startswith("<con>"))

    def test_fingerprints_ignore_the_alphabet(self):
        w1, _, _ = cf.currier_b_windows()
        lines = w1[:200]
        table = {c: chr(0xE800 + i) for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")}
        relabel = [dict(ln, words=[dict(w, word="".join(table.get(c, c) for c in w["word"])) for w in ln["words"]])
                   for ln in lines]
        a, b = cf.fingerprint(lines), cf.fingerprint(relabel, "char")
        for k in cf.PRIMARY:
            self.assertAlmostEqual(a[k], b[k], places=12, msg=k)


if __name__ == "__main__":
    unittest.main()
