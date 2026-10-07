from dataclasses import replace
import contextlib
import io
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
from voynich.decipher_search.core import Config
from voynich.laboratory.benchmark import default_plan, validate_plan, run_benchmark, control_input, main
from voynich.laboratory.fixtures import PublicInput
from voynich.decipher_search.core import digest
from voynich.search.strategies import AnnealingSearch
from tests.test_laboratory_runner import MemoryRegistry, TRAIN


class BenchmarkTests(unittest.TestCase):
    def test_plan_and_preflight_never_encrypt_or_search(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            with patch("voynich.laboratory.benchmark.FixtureBuilder.build", side_effect=AssertionError("encrypted")),                  patch("voynich.laboratory.benchmark.ExperimentRunner.run", side_effect=AssertionError("searched")),                  contextlib.redirect_stdout(io.StringIO()):
                main(["plan", str(path)])
                main(["preflight", str(path)])
                with self.assertRaises(FileExistsError):
                    main(["plan", str(path)])

    def test_tiny_coordinator_smoke_not_a_research_benchmark(self):
        # Tiny generated nonsense source; checks wiring and frozen evaluation,
        # makes no accuracy claim and touches neither real corpora nor PostgreSQL.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "uv.lock").write_text("test-lock")
            rng = random.Random(4)
            text = "".join(rng.choice("abcde ") for _ in range(2000))
            (root / "toy.txt").write_text(text)
            plan = default_plan()
            plan.update(sources={"latin": "toy.txt"}, source_hashes={"latin": digest(text)},
                        methods=["glyph"], seeds=[0], lengths=[12], steps=1, restarts=1,
                        batch_size=1, top_k=1, reservoir=1)
            store = MemoryRegistry()
            summary = run_benchmark(plan, root / "out", root=root, registry=store)
            self.assertEqual(summary["glyph"]["cases"], 1)
            self.assertEqual(len(store.rows), 4)
            self.assertTrue(all(row["sequence"] == 2 for row in store.rows.values()))
            self.assertTrue((root / "out/summary.json").exists())
            with self.assertRaises(FileExistsError):
                run_benchmark(plan, root / "out", root=root, registry=store)

    def test_controls_keep_length_spacing_and_no_truth_search(self):
        public = PublicInput("abc cab abcb aab", "prefix-unit-v1", "preserve")
        for kind in ("shuffled", "message-free", "mismatched"):
            negative = control_input(public, kind, 7)
            self.assertEqual(len(negative.ciphertext), len(public.ciphertext))
            self.assertEqual([i for i, c in enumerate(public.ciphertext) if c == " "],
                             [i for i, c in enumerate(negative.ciphertext) if c == " "])
            self.assertEqual(negative, control_input(public, kind, 7))
        with self.assertRaises(ValueError):
            AnnealingSearch(replace(public, role="evaluation"), TRAIN, Config())
        with self.assertRaises(TypeError):
            AnnealingSearch({"truth": "private"}, TRAIN, Config())
