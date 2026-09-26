"""Checks for the v101 follow-up hybrids."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("g22", Path(__file__).with_name("22_v101_gain_decomposition.py"))
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)


class HybridTests(unittest.TestCase):
    def test_letters_and_spaces_swap_independently(self):
        z, v = "qokedy.chol.dar", "qokedychol.dal"
        cols = g.align_chars(z, v)
        self.assertEqual(g.hybrid(cols, "Z", "Z"), z)
        self.assertEqual(g.hybrid(cols, "V", "V"), v)
        self.assertEqual(g.hybrid(cols, "Z", "V"), "qokedychol.dar")
        self.assertEqual(g.hybrid(cols, "V", "Z"), "qokedy.chol.dal")

    def test_letters_never_substitute_separators(self):
        for a, b in g.align_chars("ol.dy", "olxdy"):
            if a is not None and b is not None:
                self.assertEqual(g.is_sep(a), g.is_sep(b))

    def test_parse_marks_sentinels_unclean(self):
        words, gaps = g.parse_string("dar.##,chol|ok")
        self.assertEqual([w["clean"] for w in words], [True, False, True, True])
        self.assertEqual(gaps, ["ordinary", "uncertain", "drawing"])


if __name__ == "__main__":
    unittest.main()
