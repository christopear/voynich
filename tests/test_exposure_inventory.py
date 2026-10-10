import json
import unittest

from voynich.laboratory.exposure_inventory import build
from voynich.laboratory.image_annotation_packet import split
from voynich.paths import ROOT


class ExposureAndSplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = build()
        cls.split = split(cls.inventory)

    def test_inventory_matches_committed_copy(self):
        stored = json.loads((ROOT/'results/exposure_inventory_2026-10-10/inventory.json').read_text())
        self.assertEqual(json.loads(json.dumps(self.inventory['pages'])), stored['pages'])

    def test_reserved_pages_are_tier_four(self):
        tier = {p['page']: p['tier'] for p in self.inventory['pages']}
        for page in ('f26r', 'f31r', 'f39v', 'f46r', 'f94r'):
            self.assertEqual(tier[page], 4)

    def test_sets_are_bifolio_disjoint_single_hand_and_low_exposure(self):
        meta = {p['page']: p for p in self.inventory['pages']}
        groups = {name: {tuple(g) for g in s['bifolios']} for name, s in self.split['sets'].items()}
        names = list(groups)
        for i, a in enumerate(names):
            for b in names[i+1:]:
                self.assertFalse(groups[a] & groups[b])
        for name, s in self.split['sets'].items():
            for page in s['pages']:
                m = meta[page]
                self.assertEqual((m['section'], m['currier'], m['hand']), ('H', 'A', '1'))
                if name != 'development':
                    self.assertLessEqual(m['tier'], 2)
        stored = json.loads((ROOT/'results/image_annotation_pilot_2026-10-10/split.json').read_text())
        self.assertEqual(self.split['sets'], stored['sets'])


if __name__ == '__main__':
    unittest.main()
