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
