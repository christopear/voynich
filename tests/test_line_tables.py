from collections import Counter
import tempfile
from pathlib import Path
import unittest

from voynich.laboratory.rotation_pilot import controlled, page_lines, synthetic, word_hits
from voynich.laboratory.voynich_pilot import clean_page
from voynich.search.line_tables import LineTableSearch, LineTableEvaluator, phase_text, transfer
from voynich.search.strategies import Candidate
from voynich.decipher_search.core import LanguageModel

TRAINING='medicina sanat corpus herba sanat corpus et aqua frigida sanat hominem '*20


class LineTablesTests(unittest.TestCase):
    def test_independent_encoder_roundtrip(self):
        lines=('medicina sanat corpus','aqua frigida sanat','herba sanat hominem')
        for period in (1,2):
            for seed in (7,19):
                cipher,key=synthetic(lines,period,seed)
                result=LineTableEvaluator(cipher,TRAINING,period)(key)
                self.assertEqual(result.payload['plaintext'],' '.join(lines))

    def test_same_symbol_has_different_phase_readings(self):
        lines=('aa','aa')
        key=Candidate.create('line-table-v1',key={'a':'e',chr(ord('a')+65536):'i'})
        self.assertEqual(transfer(lines,2,key)['plaintext'],'ee ii')
        self.assertEqual(phase_text(('a','','a'),2),'a a')

    def test_duplicates_forbidden_within_table_but_allowed_across_tables(self):
        evaluator=LineTableEvaluator(('ab','ab'),TRAINING,2)
        key={'a':'e','b':'i',chr(ord('a')+65536):'e',chr(ord('b')+65536):'i'}
        self.assertIsNotNone(evaluator(Candidate.create('line-table-v1',key=key)).loss)
        key['b']='e'
        self.assertIsNone(evaluator(Candidate.create('line-table-v1',key=key)).loss)

    def test_unknown_is_specific_to_phase(self):
        key=Candidate.create('line-table-v1',key={'a':'e'})
        result=transfer(('a','a'),2,key)
        self.assertEqual(result['plaintext'],'e ?')
        self.assertEqual(result['code_token_coverage'],.5)

    def test_controls_preserve_lines_or_symbol_slots(self):
        lines=('ab cc','ddd a','','bb a')
        self.assertEqual(Counter(controlled(lines,'line-shuffled-1',7)),Counter(lines))
        shuffled=controlled(lines,'symbol-shuffled',7)
        self.assertEqual(Counter(''.join(lines)),Counter(''.join(shuffled)))
        self.assertEqual([len(x) for x in lines],[len(x) for x in shuffled])

    def test_missing_words_do_not_shift_line_clock(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'text'
            path.write_text('<f26r> <! $L=B $I=H>\n<f26r.1,@P0> aa.bb\n<f26r.2,+P0> ???\n<f26r.3,+P0> cc\n')
            page=clean_page(path,'f26r',include_alignment=True)
        self.assertEqual(page_lines(page),('aa bb','','cc'))

    def test_mutations_stay_valid_and_resume_is_exact(self):
        lines=('abcd abcd','dcba dcba'); evaluator=LineTableEvaluator(lines,TRAINING,2)
        search=LineTableSearch(lines,TRAINING,2,budget=32)
        for _ in range(2):
            batch=search.propose(8);values=[evaluator(c) for c in batch]
            self.assertTrue(all(v.loss is not None for v in values));search.observe(values)
        other=LineTableSearch(lines,TRAINING,2,budget=32);other.restore(search.snapshot())
        self.assertEqual([c.id for c in search.propose(8)],[c.id for c in other.propose(8)])

    def test_word_hits_ignore_short_and_unknown_words(self):
        hits=word_hits('et sanat sa?at sanat unknown',LanguageModel(TRAINING))
        self.assertEqual(hits['matched_tokens'],2)
        self.assertEqual(hits['eligible_tokens'],3)
        self.assertEqual(hits['distinct_hits'],['sanat'])


if __name__=='__main__':unittest.main()
