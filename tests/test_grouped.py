import unittest
from collections import Counter
from voynich.laboratory.grouped_boundary import fixture, control_rows, spans_from_rows
from voynich.search.grouped import GroupedProblem, GroupedEvaluator, parse_span, frozen_decode
from voynich.search.codebooks import CodebookSearch
from voynich.search.strategies import Candidate
from voynich.decipher_search.core import LanguageModel

TRAIN=('aqua calida cum vino et herba miscetur deinde bibitur contra dolorem ' * 8).strip()

class GroupedTests(unittest.TestCase):
    def test_no_fallback_or_crossing_word_boundary(self):
        self.assertEqual(parse_span('ab c',('a',),'preserve'),['ab',' ','c'])
        with self.assertRaises(ValueError):parse_span('a b',('a',),'preserve')
        self.assertEqual(parse_span('a b',('a',),'encoded'),['ab'])
        with self.assertRaises(ValueError):parse_span('ba',('a',),'encoded')

    def test_oracle_roundtrip_in_both_spacing_models(self):
        for spacing in ('preserve','encoded'):
            spans,truth,table,pref=fixture(TRAIN[:180],spacing,7)
            p=GroupedProblem(spans,TRAIN,pref,spacing)
            candidate=Candidate.create('explicit-codebook-v1',key={i:table[c] for c,i in p.ids.items()})
            result=GroupedEvaluator(p)(candidate)
            self.assertEqual(result.payload['plaintext_spans'],list(truth))
            self.assertIsNotNone(result.loss)
            decoded=frozen_decode(spans,pref,spacing,table,LanguageModel(TRAIN))
            self.assertEqual(decoded['glyph_coverage'],1)
            self.assertEqual(decoded['valid_span_fraction'],1)

    def test_unclean_words_and_drawings_break_spans(self):
        rows=[{'words':['ab',None,'cd','ef'],'gaps':['ordinary','uncertain','drawing']}]
        self.assertEqual(spans_from_rows(rows),('ab','cd','ef'))

    def test_layout_control_preserves_role_multisets(self):
        rows=[{'words':['ab','cd','ef'],'gaps':['ordinary','ordinary'],'first':True,'last':False},
              {'words':['gh','ij','kl'],'gaps':['ordinary','ordinary'],'first':True,'last':False}]
        out=control_rows(rows,'layout-1',8)
        for i in range(3):self.assertEqual(Counter(r['words'][i] for r in rows),Counter(r['words'][i] for r in out))

    def test_frozen_unknown_and_invalid_span_coverage(self):
        result=frozen_decode(('abxx','a'),('a',),'encoded',{'ab':'c'},LanguageModel(TRAIN))
        self.assertAlmostEqual(result['glyph_coverage'],2/5)
        self.assertEqual(result['valid_span_fraction'],.5)
        self.assertEqual(result['spans'][0]['plaintext'],'c??')
        self.assertEqual(result['fully_known_span_characters'],0)

    def test_grouped_beam_checkpoint_is_exact(self):
        spans,_,_,pref=fixture(TRAIN[:180],'encoded',7)
        p=GroupedProblem(spans,TRAIN,pref,'encoded');e=GroupedEvaluator(p)
        first=CodebookSearch(p,algorithm='beam',budget=32)
        batch=first.propose(8);first.observe([e(c) for c in batch])
        second=CodebookSearch(p,algorithm='beam',budget=32);second.restore(first.snapshot())
        self.assertEqual([c.data for c in first.propose(8)],[c.data for c in second.propose(8)])
