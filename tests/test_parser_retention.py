import unittest
from pathlib import Path
from voynich.decipher_search.core import normalize
from voynich.laboratory.parser_retention import retained_policies
from voynich.paths import ROOT
from voynich.storage.artifacts import read_json

class RetentionRegressionTests(unittest.TestCase):
    def test_all_eight_previously_pruned_true_parsers_survive(self):
        evidence=read_json(ROOT/'results/grouped_boundary_2026-10-09/evidence.json')
        total=0
        for row in evidence['rows']:
            if row['kind']!='synthetic':continue
            path=ROOT/('data/italian_dante.txt' if row['language']=='italian' else 'data/laboratory_sources/celsus_medical.txt')
            source=normalize(path.read_text());start=int(.3*len(source));training=source[start:start+min(12000,int(.2*len(source)))]
            policies=retained_policies(tuple(row['spans']),training,row['spacing'])
            self.assertEqual(len(policies),row['screening']['counts']['surviving'])
            self.assertIn(row['calibration']['oracle_prefixes'],[p['prefixes'] for p in policies])
            self.assertFalse(row['calibration']['oracle_policy_shortlisted'])
            total+=len(policies)
        self.assertEqual(total,177)
