"""Checks for the v101 parser and the v101 -> EVA aligner."""
import unittest
from collections import Counter

import v101


class ParserTests(unittest.TestCase):
    def test_body_separators_and_uncertainty(self):
        words, gaps, end = v101.parse_body("fa19s.9,hae.A*am.2oe=\r\n")
        self.assertEqual([w["word"] for w in words], ["fa19s", "9", "hae", "A*am", "2oe"])
        self.assertEqual(gaps, ["ordinary", "uncertain", "ordinary", "ordinary"])
        self.assertEqual(end, "=")
        self.assertFalse(words[3]["clean"])
        self.assertTrue(all(w["clean"] for i, w in enumerate(words) if i != 3))

    def test_page_names(self):
        self.assertEqual(v101.zl_page("1r"), "f1r")
        self.assertEqual(v101.zl_page("67r1"), "f67r1")
        self.assertEqual(v101.zl_page("rose"), "fRos")
        self.assertEqual(v101.zl_page("101r1-r2"), "f101r")
        self.assertEqual(v101.zl_page("101v2-v1"), "f101v")

    def test_file_parses_and_paragraphs(self):
        lines = v101.load_v101()
        text = [ln for ln in lines if ln["kind"] == "text"]
        self.assertEqual(len(lines), 4486)
        self.assertEqual(len(text), 3978)
        first = [ln for ln in text if ln["page"] == "f1r"]
        self.assertTrue(first[0]["paragraph_start"])
        # 1r.5 ends a paragraph, so 1r.6 starts one.
        self.assertTrue(first[4]["paragraph_end"] and first[5]["paragraph_start"])
        self.assertFalse(first[1]["paragraph_start"])


class AlignerTests(unittest.TestCase):
    def test_em_recovers_many_to_one_mapping(self):
        truth = {"1": "ch", "m": "iin", "o": "o", "8": "d", "9": "y", "a": "a", "2": "sh", "7": "d"}
        words = ["18a9", "o8am", "2o9", "7am", "1o9", "o7a9", "21m", "a8o", "9o1", "8m", "2a7", "o1o"]
        pairs = [(w, "".join(truth[c] for c in w)) for w in words] * 3
        mp = v101.initial_mapping(pairs)
        for _ in range(15):
            mp, _ = v101.em_step(pairs, mp)
        self.assertEqual({c: mp.best(c) for c in truth}, truth)
        self.assertEqual(v101.viterbi("18a9", "chday", mp), ["ch", "d", "a", "y"])
        table = v101.collapse_table(mp, Counter({"8": 10, "7": 3, "1": 5}))
        self.assertEqual(v101.collapse("7a8", table), "8a8")


if __name__ == "__main__":
    unittest.main()
