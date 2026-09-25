"""Regression tests for the original handoff numbers and their reconstructions.

The data-dependent tests lock the values that reproduce exactly from local
inputs, so parser or helper changes that move them are caught. They are skipped
when the downloaded corpora are absent.
"""
import unittest
from collections import Counter
from pathlib import Path

import reconstruction as rc
from voynich_core import parse_zl3b, tokenise_ivtff_body

DATA = Path(__file__).resolve().parents[1] / "data"
HAVE_DATA = all((DATA / n).exists() for n in ("ZL3b-n.txt", "naibbe_cipher_pre.txt",
                                               "naibbe_cipher_respaced.txt", "naibbe_plain_units.txt"))


class ParserTests(unittest.TestCase):
    def test_default_tokeniser_keeps_original_behaviour(self):
        self.assertEqual(tokenise_ivtff_body("dai[{cto}:@194;]y"), ["daicto", "y"])
        self.assertEqual(tokenise_ivtff_body("daiiir[{ih}:ch]y"), ["daiiirihchy"])
        self.assertEqual(tokenise_ivtff_body("da[n:r].cheo"), ["dan", "cheo"])

    def test_fixed_alternatives_keep_first_reading(self):
        fix = lambda s: tokenise_ivtff_body(s, fix_alternatives=True)
        self.assertEqual(fix("dai[{cto}:@194;]y"), ["daictoy"])
        self.assertEqual(fix("daiiir[{ih}:ch]y"), ["daiiirihy"])
        self.assertEqual(fix("da[n:r].cheo"), ["dan", "cheo"])


@unittest.skipUnless(HAVE_DATA, "downloaded corpora not present")
class ReconstructionRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pages, lines = parse_zl3b(DATA / "ZL3b-n.txt")
        cls.c = rc.Corpora(DATA, pages, lines)

    def test_controlled_subset(self):
        self.assertEqual(len(self.c.herbal_pids), 95)
        self.assertEqual(len(self.c.herbal_tokens), 8052)
        self.assertEqual(len(set(self.c.herbal_tokens)), 2468)

    def test_script01_within_line_sandhi(self):
        r = rc.stem_preserving_terminal_permutation_test(rc.terminal_records(self.c.lines))
        self.assertAlmostEqual(r["excess_mi"], 0.059405, places=5)
        self.assertAlmostEqual(r["p"], 1 / 301)

    def test_script02_missing_space_benchmark(self):
        amb = ok = 0
        for pid in self.c.herbal_pids:
            freq = Counter(w for L in self.c.herbal if L.page != pid for w in L.tokens)
            for L in (x for x in self.c.herbal if x.page == pid):
                for a, b in zip(L.tokens, L.tokens[1:]):
                    ga, gb = rc.eva_glyphs(a), rc.eva_glyphs(b)
                    if len(ga) < 2 or len(gb) < 2 or len(ga) + len(gb) > 14 or freq[a] < 2 or freq[b] < 2:
                        continue
                    cs = rc.candidate_splits(a + b, freq, boundary_bonus=0.75)
                    if len(cs) < 2 or not any(x["k"] == len(ga) for x in cs):
                        continue
                    amb += 1; ok += cs[0]["k"] == len(ga)
        self.assertEqual((amb, ok), (257, 233))

    def test_internal_m_sibling(self):
        r = rc.claim_internal_m_sibling(self.c)
        self.assertEqual((r["n_internal_m_tokens"], r["with_sibling"]), (274, 234))

    def test_rare_decomposition_counts(self):
        r = rc.claim_rare_decomposition(self.c, null_reps=1)
        self.assertEqual(r["reconstructed"]["rare_long_forms"], 3250)
        self.assertEqual(r["reconstructed"]["decomposable"], 1661)

    def test_cut_positions(self):
        r = rc.claim_cut_positions(self.c)["counts"]
        self.assertEqual((r["nlrm_cuts"], r["nlrm_hits"], r["other_cuts"], r["other_hits"]),
                         (1720, 891, 17511, 1370))

    def test_spaced_alternations(self):
        r = rc.claim_spaced_alternations(self.c)["reconstructed"]
        self.assertEqual((r["with_spaced"], r["forward_only"], r["reverse_only"]), (359, 234, 97))

    def test_rl_families(self):
        r = rc.claim_rl_families(self.c)["reconstructed"]
        self.assertEqual((r["families"], r["significant"]), (48, 16))

    def test_lopo_segmented_vocabulary(self):
        seg = self.c.lopo_segmented_herbal()
        norm = rc.conservative_normalizer(seg)
        self.assertEqual(len(set(seg)), 1991)
        self.assertEqual(len({norm(x) for x in seg}), 1640)

    def test_naibbe_localization_denominator(self):
        r = rc.claim_naibbe_localization(self.c)
        self.assertEqual((r["reconstructed"]["evaluable"], r["reconstructed"]["correct"]), (646, 632))
        self.assertEqual(r["script04_denominator"], 634)

    def test_naibbe_context_homophones(self):
        r = rc.claim_naibbe_context_homophones(self.c)["reconstructed"]
        self.assertEqual((r["frequent_types"], r["eligible"]), (178, 152))
        self.assertAlmostEqual(r["auc"], 0.748, places=3)


if __name__ == "__main__":
    unittest.main()
