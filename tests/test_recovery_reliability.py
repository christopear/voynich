import unittest
from voynich.search.grouped import GroupedProblem, GroupedEvaluator
from voynich.search.portfolio import portfolio, stability
from voynich.search.strategies import Candidate
from voynich.experiments.e42_recovery_reliability import qualify, SEEDS


class ReliabilityTests(unittest.TestCase):
    def test_portfolio_counts_both_starts_and_selects_loss(self):
        p = GroupedProblem(('AB BA',), 'the cat sat on the mat '*20, (), 'preserve')
        c = Candidate.create('test', key=dict(zip(p.ids.values(), 'at')))
        result = portfolio(GroupedEvaluator(p), c, p.units, budget=32)
        self.assertEqual(result['evaluations'], 32)
        self.assertEqual([a['evaluations'] for a in result['arms'].values()], [16, 16])
        self.assertEqual(result['best']['total_bits'], min(a['best']['total_bits'] for a in result['arms'].values()))

    def test_agreement_is_not_truth_and_excludes_shared_spaces(self):
        row = dict(prefixes=['A'], plaintext='wrong text')
        self.assertTrue(stability([row]*3)['flag'])
        self.assertFalse(stability([row, row, None])['flag'])
        self.assertFalse(stability([row, row, dict(prefixes=['B'], plaintext='wrong text')])['flag'])
        self.assertEqual(stability([dict(prefixes=[], plaintext=t) for t in ('a    b', 'a    b', 'a    c')])['minimum_agreement'], .5)

    def test_gate_does_not_pool_successful_seeds(self):
        public = {str(i): dict(language='latin' if i < 4 else 'italian', spacing='preserve' if i%2 else 'encoded') for i in range(8)}
        rows = [dict(case_id=str(i), search_seed=seed, recovery_pass=True, transfer_pass=True) for seed in SEEDS for i in range(8)]
        self.assertTrue(qualify(rows, public, True)['qualifies'])
        for row in rows:
            if row['search_seed'] == 101 and int(row['case_id']) < 3:
                row['transfer_pass'] = False
        self.assertFalse(qualify(rows, public, True)['qualifies'])
