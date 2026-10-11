import itertools
import unittest
from voynich.search.neighborhood import neighbors, audit, descend
from voynich.search.strategies import Candidate
from voynich.search.grouped import GroupedProblem, GroupedEvaluator


class NeighborhoodTests(unittest.TestCase):
    def test_complete_unique_capacity_moves(self):
        start = ('a', 'a', 'b')
        candidate = Candidate.create('test', key=dict(zip('XYZ', start)))
        actual = [tuple(c.data['key'][k] for k in 'XYZ') for c in neighbors(candidate, 'abc', 2)]
        expected = set()
        for target in itertools.product('abc', repeat=3):
            changes = [i for i in range(3) if start[i] != target[i]]
            swap = len(changes) == 2 and sorted(start[i] for i in changes) == sorted(target[i] for i in changes)
            if max(target.count(u) for u in 'abc') <= 2 and (len(changes) == 1 or swap):
                expected.add(target)
        self.assertEqual(set(actual), expected)
        self.assertEqual(len(actual), len(set(actual)))

    def test_audit_replay_and_cap(self):
        p = GroupedProblem(('AB BA',), 'the cat sat on the mat '*20, (), 'preserve')
        c = Candidate.create('codebook', key=dict(zip(p.ids.values(), 'at')))
        evaluator = GroupedEvaluator(p)
        result = audit(evaluator, c, p.units)
        replay = evaluator(Candidate.create(**result['best']['candidate']))
        self.assertEqual(replay.payload, result['best']['payload'])
        self.assertEqual(dict(replay.score.components), result['best']['components'])
        with self.assertRaises(ValueError):
            audit(evaluator, c, p.units, cap=1)

    def test_descent_budget_determinism_and_replay(self):
        p = GroupedProblem(('AB BA',), 'the cat sat on the mat '*20, (), 'preserve')
        c = Candidate.create('codebook', key=dict(zip(p.ids.values(), 'at')))
        evaluator = GroupedEvaluator(p)
        for algorithm in ('systematic', 'random'):
            result = descend(evaluator, c, p.units, algorithm=algorithm, budget=30)
            self.assertEqual(result, descend(evaluator, c, p.units, algorithm=algorithm, budget=30))
            self.assertEqual(result['evaluations'], 30)
            self.assertEqual(result['total_bits_history'], sorted(result['total_bits_history'], reverse=True))
            self.assertEqual(evaluator(Candidate.create(**result['best']['candidate'])).payload,
                             result['best']['payload'])
        self.assertTrue(descend(evaluator, c, p.units, algorithm='systematic', budget=2)['incomplete_sweep'])
