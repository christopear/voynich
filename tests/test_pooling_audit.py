import unittest
from voynich.experiments.posthoc_e27_pooling import pool

class PoolingAuditTests(unittest.TestCase):
    def test_identity_ties_are_position_independent(self):
        tokens = [str(i) for i in range(1024)]
        values = pool(tokens, 7)
        reversed_values = pool(tokens[::-1], 7)[::-1]
        self.assertEqual(values, reversed_values)
        self.assertEqual(sum(v[0] == 0 for v in values), 200)

    def test_frequency_outranks_hash(self):
        tokens = ['frequent']*20 + [str(i) for i in range(1024)]
        for seed in (7,19,31):
            self.assertEqual(pool(tokens, seed)[0], (0,'frequent'))
