from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from voynich.laboratory.medical_report import build_report,compile_evidence
from voynich.storage.artifacts import write_json,read_json

class MedicalReportTests(unittest.TestCase):
    def files(self,path):
        row={'case':'<script>bad</script>','target':'celsus','training_author':'pliny','algorithm':'beam','family':'glyph',
            'run_ids':{'positive':'p','token-shuffled':'n'},'metrics':{'nonspace_edit_accuracy':.99},
            'selected_loss':1.0,'oracle_loss':1.1,'oracle_score':{'components':[['language_bits',11.0]],'denominator':10},
            'screening_gate':True,'diagnosis':'recovered-at-development-threshold','boundary_f1':1,
            'frozen':{'metrics':{'nonspace_edit_accuracy':.99},'code_token_coverage':1,'plaintext':'a ? b'},
            'beats_shuffled':True,'invalid_candidates':{'positive':0},'truth_nll_narrative_per_character':3,
            'truth_nll_medical_per_character':2,'examples':{'truth':'ab','recovered':'af','ciphertext':'XY','frozen_truth':'ab'}}
        summary={'status':'completed','cases':[row],'plan':{'families':['glyph'],'algorithms':['beam']},'total_evaluations':20}
        write_json(path/'summary.json',summary)
        for name in ('p','n'):
            write_json(path/'runs'/name/'summary.json',{'run_id':name,'spec_id':'spec','evaluations':10,'failures':0,
                'top':[{'score':{'components':[['language_bits',10.0]]}}],
                'strategy_diagnostics':{},'stop_reason':'evaluation-limit','state':'stopped'})
            write_json(path/'runs'/name/'manifest.json',{'environment':{'test':True}})
        audit=path/'audit.json';write_json(audit,{'cases':[]})
        return audit

    def test_near_correct_objective_error_is_visible_without_rewriting_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);audit=self.files(root)
            original=read_json(root/'summary.json')
            evidence=compile_evidence(root,audit)
            row=evidence['study']['cases'][0]
            self.assertTrue(row['posthoc_objective_prefers_inexact'])
            self.assertTrue(row['screening_gate'])
            self.assertEqual(row['diagnosis'],'recovered-at-development-threshold')
            self.assertEqual(row['posthoc_cost_gap_bits']['language_bits'],-1)
            self.assertEqual(read_json(root/'summary.json'),original)
            report=build_report(evidence,root/'export').read_text()
            self.assertIn('&lt;script&gt;bad&lt;/script&gt;',report)
            self.assertNotIn('<script>bad</script>',report)

    def test_export_rejects_missing_runs_or_unreconciled_totals(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);audit=self.files(root)
            summary=read_json(root/'summary.json');summary['total_evaluations']=19
            write_json(root/'summary.json',summary,replace=True)
            with self.assertRaises(ValueError):compile_evidence(root,audit)
            summary['total_evaluations']=20;write_json(root/'summary.json',summary,replace=True)
            (root/'runs/n/summary.json').unlink()
            with self.assertRaises(ValueError):compile_evidence(root,audit)
