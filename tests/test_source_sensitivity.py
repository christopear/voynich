import json
import unittest

from voynich.experiments.e34_source_sensitivity import source_data
from voynich.laboratory.forward_screen import passages, source_frequencies, vocabulary


class SourceSensitivityTests(unittest.TestCase):
    def test_cucina_inputs_equal_stage_33_inputs(self):
        vocab, freqs, panels = source_data('cucina')
        self.assertEqual(vocab, vocabulary())
        self.assertEqual(freqs, source_frequencies())
        self.assertEqual(json.dumps(panels), json.dumps(passages()))

    def test_medical_passages_are_chapter_disjoint(self):
        for source in ('celsus', 'pliny'):
            _, freqs, panels = source_data(source)
            dev = {s['chapter'] for p in panels if p['split'] == 'development' for s in p['spans']}
            val = {s['chapter'] for p in panels if p['split'] == 'validation' for s in p['spans']}
            self.assertTrue(dev.isdisjoint(val))
            self.assertTrue(all(len(p['words']) == 512 for p in panels))
            self.assertTrue(all(w in freqs for p in panels for w in p['words']))


if __name__ == '__main__':
    unittest.main()
