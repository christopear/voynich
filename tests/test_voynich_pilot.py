import tempfile
from pathlib import Path
import unittest
from collections import Counter

from voynich.laboratory.voynich_pilot import clean_page, represent, control_text, language_metrics
from voynich.decipher_search.core import LanguageModel


class VoynichPilotTests(unittest.TestCase):
    def test_uncertain_tokens_never_become_plain_words(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'source.txt'
            path.write_text('<f26r> <! $L=B $I=H>\n<f26r.1,@P0> <%>chedy.da?.[s:r]ar.@138;aiin.s,aiin.che{ph}dy<->daiin<$>\n')
            page = clean_page(path, 'f26r')
        self.assertEqual(page['words'], ['chedy', 'daiin'])
        self.assertEqual(len(page['omitted']), 5)
        self.assertEqual(page['raw_line_span'], [1, 2])

    def test_compounds_stable_between_pages_and_reversible(self):
        left, labels = represent(['chedy', 'cthy'], 'compounds')
        right, _ = represent(['cthy', 'chedy'], 'compounds')
        self.assertEqual(left.split(), right.split()[::-1])
        self.assertEqual(''.join(' ' if c == ' ' else labels[c] for c in left), 'chedy cthy')

    def test_controls_preserve_declared_invariants(self):
        text = 'ab abcd a bbcc'
        shuffled = control_text(text, 'symbol-shuffled', 5)
        self.assertEqual(Counter(text), Counter(shuffled))
        self.assertEqual([i for i,c in enumerate(text) if c==' '], [i for i,c in enumerate(shuffled) if c==' '])
        self.assertEqual(Counter(text.split()), Counter(control_text(text, 'word-shuffled', 5).split()))
        self.assertEqual(shuffled, control_text(text, 'symbol-shuffled', 5))

    def test_unknown_words_are_not_scored_or_joined(self):
        lm = LanguageModel('medicina sanat corpus herba sanat corpus '*10)
        metrics = language_metrics('medicina sa?at corpus', lm)
        self.assertEqual(metrics['scored_characters'], len('medicinacorpus'))
        expected = (lm.nll('medicina')+lm.nll('corpus'))/len('medicinacorpus')
        self.assertAlmostEqual(metrics['bits_per_character'], expected)
        self.assertIsNone(language_metrics('???', lm)['bits_per_character'])


if __name__ == '__main__':
    unittest.main()
