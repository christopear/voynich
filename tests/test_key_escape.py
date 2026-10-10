import unittest
from voynich.search.key_escape import anneal, move_descriptors, apply_move
from voynich.search.neighborhood import neighbors
from voynich.search.grouped import GroupedProblem, GroupedEvaluator
from voynich.search.strategies import Candidate


class KeyEscapeTests(unittest.TestCase):
    def test_descriptor_order_matches_exhaustive_neighborhood(self):
        candidate = Candidate.create('test', key={'X': 'a', 'Y': 'a', 'Z': 'b'})
        self.assertEqual([apply_move(candidate, m) for m in move_descriptors(candidate, 'abc')],
                         list(neighbors(candidate, 'abc', 2)))

    def test_budget_replay_and_best_retention(self):
        p = GroupedProblem(('AB BA AB',), 'the cat sat on the mat '*20, (), 'preserve')
        c = Candidate.create('test', key=dict(zip(p.ids.values(), 'at')))
        evaluator = GroupedEvaluator(p)
        result = anneal(evaluator, c, p.units, budget=80)
        self.assertEqual(result, anneal(evaluator, c, p.units, budget=80))
        self.assertEqual(result['evaluations'], 80)
        costs = [r['total_bits'] for r in result['best_history']]
        self.assertEqual(costs, sorted(costs, reverse=True))
        self.assertEqual(evaluator(Candidate.create(**result['best']['candidate'])).payload,
                         result['best']['payload'])
