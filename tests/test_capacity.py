"""The information-capacity screen must pass families that can work and exclude ones that cannot."""
import random
import unittest

from voynich.evaluation import capacity as cap

SIZE = 5000


class CapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.latin = cap.reference_units(cap.REFERENCES["latin_celsus_medical"][0])[:60000]
        cls.plain = cap.entropy_profile(cls.latin, size=SIZE)

    def check(self, units, state_bits=0.0):
        return cap.length_preserving_check(cap.entropy_profile(units, size=SIZE), self.plain, state_bits)

    def test_bijective_substitution_of_latin_is_feasible(self):
        letters = sorted(set(self.latin) - {cap.SPACE})
        shuffled = letters[:]
        random.Random(1).shuffle(shuffled)
        table = dict(zip(letters, shuffled), **{cap.SPACE: cap.SPACE})
        self.assertTrue(self.check([table[u] for u in self.latin])["feasible"])

    def test_homophonic_encipherment_of_latin_is_feasible(self):
        rng = random.Random(2)
        units = [u if u == cap.SPACE else u + str(rng.randrange(2)) for u in self.latin]
        self.assertTrue(self.check(units)["feasible"])

    def test_voynich_single_table_is_excluded(self):
        units = cap.voynich_units()["compound EVA"][:60000]
        result = self.check(units)
        self.assertFalse(result["feasible"])
        self.assertGreater(result["by_order"][3]["gap_bits"], 1.0)

    def test_verbose_code_fails_length_preserving_but_shows_expansion(self):
        # Each letter becomes a fixed two-symbol code over a 6-symbol alphabet.
        letters = sorted(set(self.latin) - {cap.SPACE})
        codes = [a + b for a in "abcdef" for b in "abcdef"]
        table = dict(zip(letters, codes))
        verbose = []
        for u in self.latin:
            verbose.extend([cap.SPACE] if u == cap.SPACE else list(table[u]))
        self.assertFalse(self.check(verbose)["feasible"])
        ratio = cap.required_expansion(verbose, self.latin, m=2, size=SIZE)["units_per_symbol"]
        self.assertTrue(1.0 < ratio <= 2.5, ratio)


if __name__ == "__main__":
    unittest.main()
