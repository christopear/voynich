from dataclasses import replace
import json
import unittest
from voynich.ciphers.units import UnitCipher
from voynich.decipher_search.core import Config
from voynich.evaluation.scorers import KeyEvaluator
from voynich.laboratory.fixtures import PublicInput
from voynich.laboratory.oracle_audit import classify_gap
from voynich.search.codebooks import CodebookProblem,CodebookEvaluator,CodebookSearch,tokenize,partial_transfer
from voynich.search.strategies import Candidate

TRAIN='in principio erat verbum et verbum erat apud deum '*15

class CodebookTests(unittest.TestCase):
    def fixture(self,method,plain='in principio erat verbum'):
        key=method.generate_key(seed=7)
        cipher,alignment=method.encrypt_text(plain,key,seed=8)
        active={cipher[a:b] for _,_,a,b in alignment}-{' '}
        candidate=Candidate.create('explicit-codebook-v1',key={c:key.as_mapping()[c] for c in active},
            long_prefixes=sorted({c[0] for c in key.as_mapping() if len(c)==2}))
        return PublicInput(cipher,method.method_id,'preserve'),candidate

    def test_fixed_and_variable_group_oracle_needs_no_character_fallback(self):
        for lengths in ('fixed','variable'):
            method=UnitCipher('groups',lengths=lengths,extra_units=('in','er'))
            public,candidate=self.fixture(method)
            problem=CodebookProblem(public,TRAIN,method.units,2 if lengths=='fixed' else None)
            value=CodebookEvaluator(problem)(candidate)
            self.assertEqual(value.payload['plaintext'],'in principio erat verbum')
            self.assertIsNotNone(value.loss)
            self.assertEqual(''.join(value.payload['tokens']),public.ciphertext)
            self.assertTrue(any(len(c)==2 for c in candidate.data['key']))

    def test_boundaries_cannot_be_crossed(self):
        for text in ('ABC','A BC','AB C'):
            with self.assertRaises(ValueError):tokenize(text,2)
        self.assertEqual([c for c,_,_ in tokenize('ABAB C',None,{'A'})],['AB','AB',' ','C'])

    def test_score_matches_existing_objective_for_active_fixed_key(self):
        for family,homophones in (('glyph',1),('glyph',2),('groups',1)):
            method=UnitCipher(family,homophones=homophones)
            public,candidate=self.fixture(method)
            problem=CodebookProblem(public,TRAIN,method.units,1 if family=='glyph' else 2,homophones)
            reference=KeyEvaluator(public,TRAIN,Config(family=family,pair_units=0))(candidate)
            value=CodebookEvaluator(problem)(candidate)
            self.assertAlmostEqual(reference.loss,value.loss,places=10)

    def test_strategies_share_initial_states_and_resume_exactly(self):
        method=UnitCipher();public,_=self.fixture(method)
        problem=CodebookProblem(public,TRAIN)
        a=CodebookSearch(problem,algorithm='annealing',budget=80,width=4)
        b=CodebookSearch(problem,algorithm='beam',budget=80,width=4)
        self.assertEqual(a.propose(4),b.propose(4))
        for strategy in (a,b):
            evaluator=CodebookEvaluator(problem)
            strategy.observe([evaluator(c) for _,c in strategy.pending])
            for _ in range(4):strategy.observe([evaluator(c) for c in strategy.propose(4)])
            state=json.loads(json.dumps(strategy.snapshot()))
            clone=CodebookSearch(problem,algorithm=strategy.algorithm,budget=80,width=4)
            clone.restore(state)
            self.assertEqual(strategy.propose(4),clone.propose(4))
            self.assertTrue(all(v<=1 for c in clone.pending for v in __import__('collections').Counter(c[1].data['key'].values()).values()))

    def test_frozen_unknown_code_remains_explicit_and_does_not_mutate_key(self):
        candidate=Candidate.create('explicit-codebook-v1',key={'AB':'e'},long_prefixes=[])
        problem=CodebookProblem(PublicInput('AB CD AB','test','preserve','evaluation'),TRAIN,width=2)
        result=partial_transfer(problem,candidate)
        self.assertEqual(result['plaintext'],'e ? e')
        self.assertAlmostEqual(result['code_token_coverage'],2/3)
        self.assertEqual(result['unknown_codes'],['CD'])
        self.assertEqual(candidate.data['key'],{'AB':'e'})
        with self.assertRaises(ValueError):CodebookSearch(problem)

    def test_capacity_and_unused_keys_are_rejected(self):
        problem=CodebookProblem(PublicInput('ABAB','test','preserve'),TRAIN)
        for key in ({'A':'a','B':'a'},{'A':'a','B':'b','C':'c'}):
            self.assertIsNone(CodebookEvaluator(problem)(Candidate.create('explicit-codebook-v1',key=key)).loss)

    def test_gap_labels_distinguish_objective_search_and_representation(self):
        self.assertEqual(classify_gap(.4,2,3),'search-gap-demonstrated')
        self.assertEqual(classify_gap(.4,3,2),'objective-prefers-or-ties-found-wrong-answer')
        self.assertEqual(classify_gap(.4,2,3,False),'representation-mismatch')

    def test_medical_extraction_rejects_ambiguous_editions(self):
        from voynich.acquisition.medical_corpora import extract_books
        xml='<TEI><div subtype="book" n="1"><p>her<hi>ba</hi><note>note</note> aqua <foreign>greek</foreign> calida</p></div></TEI>'
        self.assertEqual(extract_books(xml,('1',)),'herba aqua calida')
        with self.assertRaises(ValueError):extract_books(xml,('2',))
        with self.assertRaises(NotImplementedError):extract_books(xml.replace('<hi>ba</hi>','<choice>ba</choice>'),('1',))

    def test_matched_control_preserves_code_counts_and_space_positions(self):
        from collections import Counter
        from voynich.laboratory.medical_recovery import shuffled_codes
        method=UnitCipher('groups',lengths='variable',extra_units=('in','er'))
        key=method.generate_key(seed=7)
        text,alignment=method.encrypt_text('in principio erat verbum '*5,key,seed=8)
        shuffled=shuffled_codes(text,alignment,19)
        before=[text[a:b] for _,_,a,b in alignment]
        after=[shuffled[a:b] for _,_,a,b in alignment]
        self.assertEqual(Counter(before),Counter(after))
        self.assertEqual([i for i,c in enumerate(text) if c==' '],[i for i,c in enumerate(shuffled) if c==' '])
        self.assertNotEqual(text,shuffled)
        self.assertEqual(shuffled,shuffled_codes(text,alignment,19))

    def test_beam_best_cost_does_not_regress_and_obeys_budget(self):
        public,_=self.fixture(UnitCipher())
        problem=CodebookProblem(public,TRAIN)
        strategy=CodebookSearch(problem,algorithm='beam',budget=71,width=4)
        evaluator=CodebookEvaluator(problem);previous=float('inf');count=0
        while candidates:=strategy.propose(3):
            strategy.observe([evaluator(c) for c in candidates]);count+=len(candidates)
            costs=[row['loss'] for row in strategy.pool if row['loss'] is not None]
            if costs:
                self.assertLessEqual(min(costs),previous)
                previous=min(costs)
        self.assertEqual(count,71)
        self.assertEqual(strategy.evaluated,71)

    def test_unknown_mapping_counts_match_exhaustive_assignments(self):
        import itertools
        from collections import Counter
        from voynich.ciphers.ambiguity import count_mapping_completions
        units=('a','b','in');known={'X':'a'}
        for capacity in (1,2):
            for missing in range(5):
                expected=0
                for assignment in itertools.product(units,repeat=missing):
                    counts=Counter(assignment)+Counter(known.values())
                    expected+=all(n<=capacity for n in counts.values())
                self.assertEqual(count_mapping_completions(known,units,capacity,missing),expected)
        self.assertEqual(count_mapping_completions({},tuple('abcd'),1,2),12)
        with self.assertRaises(NotImplementedError):count_mapping_completions({},('herba',),1,1)

    def test_medical_plan_rejects_silent_gate_changes_and_source_leakage(self):
        from copy import deepcopy
        from pathlib import Path
        from voynich.paths import ROOT
        from voynich.laboratory.medical_recovery import validate_plan
        from voynich.storage.artifacts import read_json
        plan=read_json(ROOT/'configs/benchmarks/medical-recovery-2026-10-08.json')
        corpora={n:{'text':'a'*700000} for n in ('celsus','pliny')}
        self.assertEqual(validate_plan(plan,corpora)['maximum_evaluations'],512000)
        for change in ('controls','budget','source','gate','seeds'):
            bad=deepcopy(plan)
            if change=='controls':bad['controls']=['positive']
            elif change=='budget':bad['budget']=0
            elif change=='source':bad['frozen_fraction']=bad['development_fraction']
            elif change=='gate':bad['criteria']['complete_frozen_codes']=False
            else:bad['seeds']=[7,7]
            with self.subTest(change=change),self.assertRaises(ValueError):validate_plan(bad,corpora)
