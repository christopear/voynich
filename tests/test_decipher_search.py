import random
import unittest
import contextlib
import io
import json
from pathlib import Path
import tempfile

from voynich.decipher_search.core import (Config, LanguageModel, decode, edit_accuracy, evaluate,
                                 inventory, mutate, normalize, prepare_cipher,
                                 search_restart, synthetic)
from voynich.decipher_search.cli import frozen_evaluation, main, negative_cipher, split_fixture


TRAIN = ("in principio erat verbum et verbum erat apud deum et deus erat verbum "
         "aqua est bona et terra est magna in terra sunt herbae et flores ") * 30


class LanguageTests(unittest.TestCase):
    def test_normalization_is_explicit(self):
        self.assertEqual(normalize("Jūvat æquum, œil: VITA!"), "juvat aequum oeil vita")

    def test_conditional_probabilities_sum_to_one(self):
        for order in (1, 4):
            lm = LanguageModel(TRAIN, order)
            for context in ("^^^", "est", "zzz", ""):
                self.assertAlmostEqual(sum(2 ** -lm.cost(context, c) for c in lm.alphabet), 1)

    def test_incremental_equals_full_score(self):
        lm = LanguageModel(TRAIN)
        a, state = lm.extend("^^^", "in prin")
        b, _ = lm.extend(state, "cipio")
        self.assertAlmostEqual(a + b, lm.nll("in principio"))

    def test_training_text_changes_score(self):
        latin = LanguageModel(TRAIN)
        self.assertLess(latin.nll("in principio erat"), latin.nll("xz qwzxxpp zzzzzq"))


class DecoderTests(unittest.TestCase):
    def setUp(self):
        self.lm = LanguageModel(TRAIN)

    def test_known_key_all_families(self):
        truth = "in principio erat verbum et aqua est bona in terra"
        for family in ("glyph", "groups", "mixed"):
            for homophones in (1, 2):
                cipher, key, path = synthetic(truth, family, 12, homophones)
                result = decode(cipher, key, self.lm, 8)
                self.assertTrue(result["valid"])
                self.assertEqual(result["plaintext"], truth)
                self.assertEqual("".join(result["path"]), cipher)
                self.assertEqual("".join(path), cipher)

    def test_ambiguous_segmentation_matches_exhaustive_search(self):
        key = {"x": "a", "xx": "in", "xxx": "et"}
        def paths(n):
            if not n:
                yield []
            for k in (1, 2, 3):
                if k <= n:
                    for tail in paths(n - k):
                        yield ["x" * k] + tail
        scores = [(self.lm.nll("".join(key[c] for c in p)), p) for p in paths(5)]
        got = decode("xxxxx", key, self.lm, 100)
        self.assertAlmostEqual(got["path_bits"], min(s for s, _ in scores))

    def test_homophone_choice_cost(self):
        got = decode("xy", {"x": "a", "y": "a"}, self.lm, 8)
        self.assertAlmostEqual(got["encoding_choice_bits"], 2)

    def test_no_silent_unknown_or_null(self):
        self.assertFalse(decode("xyz", {"x": "a"}, self.lm, 8)["valid"])
        with self.assertRaises(ValueError):
            decode("x", {"x": ""}, self.lm, 8)
        with self.assertRaises(ValueError):
            prepare_cipher("<f1r> da?in", "preserve")

    def test_preserve_spaces_prevents_cross_boundary_code(self):
        got = decode("x x", {"x": "a", "xx": "in"}, self.lm, 8)
        self.assertEqual(got["plaintext"], "a a")

    def test_inferred_spaces_are_emitted_by_key(self):
        got = decode(prepare_cipher("x y z", "infer"), {"x": "in", "y": " ", "z": "terra"}, self.lm, 8)
        self.assertEqual(got["plaintext"], "in terra")

    def test_whole_word_codes_cannot_emit_inside_preserved_words(self):
        key = {"x": "terra", "y": "a"}
        self.assertFalse(decode("xy", key, self.lm, 8, word_boundaries=True)["valid"])
        self.assertEqual(decode("x y", key, self.lm, 8, word_boundaries=True)["plaintext"], "terra a")


class SearchTests(unittest.TestCase):
    def test_search_cli_writes_frozen_evaluation_and_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "train.txt").write_text(TRAIN)
            (root / "dev.txt").write_text("xxx xx x")
            (root / "eval.txt").write_text("xy xx")
            args = ["search", "--train", str(root / "train.txt"), "--language", "latin",
                    "--cipher", str(root / "dev.txt"), "--evaluation", str(root / "eval.txt"),
                    "--output", str(root / "result.json"), "--steps", "2", "--restarts", "1"]
            with contextlib.redirect_stdout(io.StringIO()):
                main(args)
            result = json.loads((root / "result.json").read_text())
            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["evaluations"], 3)
            self.assertIn("core.py", result["provenance"]["implementation_sha256"])
            self.assertFalse(result["evaluation"]["candidates"][0]["valid"])

    def test_cli_help(self):
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as exit:
            main(["--help"])
        self.assertEqual(exit.exception.code, 0)

    def test_reproducible_search_and_archive(self):
        cfg = Config(steps=30, restarts=1)
        one = search_restart("xyz xy xz yx", TRAIN, cfg, 0)
        two = search_restart("xyz xy xz yx", TRAIN, cfg, 0)
        self.assertEqual(one, two)
        scores = [c["score"] for c in one["candidates"]]
        self.assertEqual(scores, sorted(scores))
        self.assertEqual(one["evaluations"], 31)
        self.assertTrue(all(c["exact_cipher_coverage"] for c in one["candidates"]))

    def test_mutations_keep_singleton_coverage_and_limits(self):
        cfg = Config(family="mixed", extra_codes=2)
        rng = random.Random(0)
        key = {"x": "a", "y": "b"}
        for _ in range(300):
            key = mutate(key, ["xx", "xy", "yx", "yy"], ["a", "b", "ab"], cfg, rng)
            self.assertIn("x", key)
            self.assertIn("y", key)
            self.assertLessEqual(sum(len(k) > 1 for k in key), 2)
            self.assertTrue(all(key.values()))

    def test_frozen_evaluation_does_not_fill_unknown_symbols(self):
        cfg = Config(steps=1)
        from dataclasses import asdict
        result = {"config": asdict(cfg), "candidates": [{"key": {"x": "a"}}]}
        got = frozen_evaluation(result, "xy", TRAIN)
        self.assertFalse(got["key_refitted"])
        self.assertFalse(got["candidates"][0]["valid"])
        self.assertEqual(result["candidates"][0]["key"], {"x": "a"})

    def test_controls_split_before_lm_fit(self):
        source = " ".join(["alpha"] * 700 + ["beta"] * 50 + ["gamma"] * 100 + ["delta"] * 150)
        training, dev, test, cipher, evaluation, key = split_fixture(source, "glyph", 1, 100, 1)
        self.assertEqual(set(training.split()), {"alpha"})
        self.assertEqual(set(dev.split()), {"gamma"})
        self.assertEqual(set(test.split()), {"delta"})
        self.assertEqual(decode(evaluation, key, LanguageModel(training), 8)["plaintext"], test)

    def test_fixture_emissions_respect_training_inventory(self):
        cfg = Config(family="mixed", pair_units=2, word_units=2)
        training, _, _, _, _, key = split_fixture(TRAIN, "mixed", 1, 20, 1, cfg)
        allowed = set(inventory(LanguageModel(training), cfg))
        self.assertTrue(set(key.values()) <= allowed)

    def test_controls_preserve_slots_and_shuffle_counts(self):
        text = "abc aa defg hijk"
        for kind in ("shuffled", "assembly", "mismatched"):
            got = negative_cipher(text, kind, 2)
            self.assertEqual([len(w) for w in got.split()], [len(w) for w in text.split()])
            if kind != "assembly":
                self.assertEqual(sorted(got), sorted(text))

    def test_edit_accuracy(self):
        self.assertEqual(edit_accuracy("abc", "abc"), 1)
        self.assertAlmostEqual(edit_accuracy("axc", "abc"), 2 / 3)

    def test_invalid_config(self):
        for cfg in (Config(steps=0), Config(beam=0), Config(temperature_end=-1), Config(family="anything")):
            with self.assertRaises(ValueError):
                cfg.validate()


if __name__ == "__main__":
    unittest.main()
