from dataclasses import replace
import random
import unittest
from voynich.ciphers.units import UnitCipher
from voynich.decipher_search.core import Config
from voynich.evaluation.glyph import GlyphEvaluator
from voynich.evaluation.scorers import KeyEvaluator
from voynich.laboratory.corpora import greek_encode, greek_decode, greek_normalize, GREEK
from voynich.laboratory.fixtures import PublicInput
from voynich.search.monoalphabetic import MonoalphabeticSearch
from voynich.search.strategies import Candidate

TRAIN="in principio erat verbum et verbum erat apud deum "*10


class OperatingTests(unittest.TestCase):
    def test_greek_storage_mapping_is_bijective_after_declared_normalization(self):
        self.assertEqual(len(GREEK),24)
        self.assertEqual(len(set(GREEK.values())),24)
        text="Μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος"
        self.assertEqual(greek_decode(greek_encode(text)),greek_normalize(text))
        self.assertEqual(greek_encode("σς"),"ss")
        with self.assertRaises(NotImplementedError):
            greek_encode("ϝ")

    def test_exact_glyph_cost_matches_existing_decoder(self):
        for homophones in (1,2):
            for seed in range(8):
                method=UnitCipher(homophones=homophones)
                key=method.generate_key(seed=seed)
                text,_=method.encrypt_text("in principio erat verbum",key,seed=seed+1)
                public=PublicInput(text,method.method_id,"preserve")
                candidate=Candidate.create("search-key-v1",key=key.as_mapping())
                reference=KeyEvaluator(public,TRAIN,Config())(candidate)
                fast=GlyphEvaluator(public,TRAIN,Config())(candidate)
                self.assertEqual(fast.payload["plaintext"],reference.payload["plaintext"])
                self.assertAlmostEqual(fast.loss,reference.loss,places=10)

    def test_injective_proposals_and_checkpoint_restore(self):
        public=PublicInput("abc ab cad","prefix-unit-v1","preserve")
        config=Config(steps=30,restarts=2)
        search=MonoalphabeticSearch(public,TRAIN,config)
        scorer=GlyphEvaluator(public,TRAIN,config)
        for _ in range(12):
            proposals=search.propose(2)
            for candidate in proposals:
                values=list(candidate.data["key"].values())
                self.assertEqual(len(set(values)),len(values))
            search.observe([scorer(c) for c in proposals])
        saved=search.snapshot()
        second=MonoalphabeticSearch(public,TRAIN,config)
        second.restore(saved)
        self.assertEqual(search.propose(2),second.propose(2))

    def test_shift_search_exhausts_unique_keys_and_resumes(self):
        from voynich.search.shifts import ShiftSearch,shift_key
        search=ShiftSearch()
        first=search.propose(9)
        restored=ShiftSearch()
        restored.restore(search.snapshot())
        remaining=search.propose(50)
        self.assertEqual(remaining,restored.propose(50))
        self.assertEqual(len(first+remaining),26)
        self.assertEqual(len({c.id for c in first+remaining}),26)
        self.assertEqual(shift_key(3)["d"],"a")
        with self.assertRaises(ValueError):
            shift_key(26)

    def test_report_escapes_text_and_handles_invalid_metrics(self):
        import tempfile
        from pathlib import Path
        from voynich.laboratory.report import build_report
        evidence={
            "roundtrips":{"cases":[],"sources":[],"examples":[],
                "summary":{"cases":0,"reference_exact":0,"page_exact":0,"page_cases":0}},
            "baseline":{"cases":[{"case":"<script>bad</script>","metrics":None,"frozen":None,
                "engineering_gate_pass":False,"search_space":{"in_search_space":False},"method":"glyph"}]},
            "focused":{"cases":[]},"page_recovery":{"summary":{"cases":0,"choices_exact":0}},
            "shift_recovery":{"summary":{"cases":0,"key_exact":0,"frozen_exact":0}},
            "runs":[],"total_search_evaluations":0,"execution_errors":0}
        with tempfile.TemporaryDirectory() as directory:
            path=build_report(evidence,Path(directory)/"report")
            text=path.read_text()
            self.assertIn("&lt;script&gt;bad",text)
            self.assertNotIn("<script>bad",text)
            self.assertIn("evidence.json",text)


    def test_tei_excludes_editorial_material_and_preserves_inline_tails(self):
        import tempfile
        from pathlib import Path
        from voynich.laboratory.corpora import tei_body
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.xml"
            path.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader>header</teiHeader>'
                '<text><body><div><head>title</head><p>ar<hi>ma</hi> virum'
                '<note>editorial</note> que</p><p>cano</p></div></body></text></TEI>')
            self.assertEqual(tei_body(path),"arma virum que cano")


    def test_inventory_coverage_does_not_hide_forced_code_mismatch(self):
        from voynich.laboratory.fixtures import FixtureBuilder
        from voynich.ciphers.models import TextSource
        method=UnitCipher("mixed",lengths="variable",extra_units=("in",))
        fixture=FixtureBuilder(method).build(TextSource("bbbb bbbb",("latin",),"toy"),seed=7)
        result=fixture.search_space(TRAIN,Config(family="mixed"))
        self.assertFalse(result["in_search_space"])
        self.assertTrue(result["forced_codes_absent_from_truth"])
        self.assertIn("cannot remove",result["reasons"][0])
