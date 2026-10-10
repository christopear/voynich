import unittest
from unittest.mock import patch

from voynich.search.grouped import GroupedProblem, GroupedEvaluator, screen_policies
from voynich.search.grouped_pipeline import beam, recover
from voynich.search.strategies import Candidate
from voynich.experiments.e40_fresh_recovery import intervals_overlap


class GroupedPipelineTests(unittest.TestCase):
    def test_beam_budget_and_exact_replay(self):
        p = GroupedProblem(('AB BA AB',), 'the cat sat on the mat '*20, (), 'preserve')
        result = beam(p, 31, budget=32)
        self.assertEqual(result['evaluations'], 32)
        self.assertEqual(result, beam(p, 31, budget=32))
        replay = GroupedEvaluator(p)(Candidate.create(**result['best']['candidate']))
        self.assertEqual(replay.payload, result['best']['payload'])
        self.assertEqual(replay.loss, result['loss'])

    def test_over_cap_does_not_search_subset(self):
        with patch('voynich.search.grouped_pipeline.screen_policies', return_value={
                'survivors': [{'prefixes': ['A']}, {'prefixes': ['B']}]}), patch(
                'voynich.search.grouped_pipeline.beam') as search:
            result = recover(('AB',), 'abc '*100, 'preserve', 31, policy_cap=1)
        self.assertEqual(result['status'], 'parser_budget_cap')
        search.assert_not_called()

    def test_interval_boundaries(self):
        self.assertFalse(intervals_overlap((0, 350), (350, 700)))
        self.assertTrue(intervals_overlap((0, 350), (349, 700)))

    def test_complete_pipeline_keeps_every_survivor_and_charges_calls(self):
        spans, training = ('ABAB ABAB',), 'the cat sat on the mat '*20
        result = recover(spans, training, 'preserve', 31, beam_budget=16, continuation_budget=16)
        expected = sorted(screen_policies(spans, training, 'preserve')['survivors'],
                          key=lambda p: p['prefixes'])
        self.assertEqual([w['policy'] for w in result['policies']], expected)
        self.assertEqual(result['evaluations'], 16*len(expected)+16)
        self.assertLessEqual(result['refined']['best']['total_bits'], result['selected']['best']['total_bits'])
        problem = GroupedProblem(spans, training, tuple(result['selected']['policy']['prefixes']), 'preserve')
        replay = GroupedEvaluator(problem)(Candidate.create(**result['refined']['best']['candidate']))
        self.assertEqual(replay.payload, result['refined']['best']['payload'])
