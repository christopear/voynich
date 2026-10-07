from dataclasses import replace
import copy
import json
from pathlib import Path
import tempfile
import unittest
import uuid
from voynich.decipher_search.core import Config
from voynich.evaluation.scorers import KeyEvaluator
from voynich.experiments.runner import ExperimentRunner
from voynich.laboratory.fixtures import PublicInput
from voynich.laboratory.manifest import fingerprint
from voynich.search.strategies import AnnealingSearch
from voynich.storage.registry import DuplicateExperiment
from tests.test_laboratory_manifest import specification

TRAIN = "in principio erat verbum et verbum erat apud deum " * 5


class MemoryRegistry:
    """Transactional test double; actual SQL transactions tested separately."""
    def __init__(self):
        self.rows = {}
        self.records = []

    def register(self, spec, artifact_dir, *, rerun_reason=None):
        if any(v["spec_id"] == spec.id for v in self.rows.values()) and not rerun_reason:
            raise DuplicateExperiment("duplicate")
        key = str(uuid.uuid4())
        self.rows[key] = {"spec_id": spec.id, "artifact_dir": artifact_dir, "sequence": 0,
                          "checkpoint": None, "state": "created"}
        return key

    def get(self, run_id):
        return copy.deepcopy(self.rows[run_id])

    def commit_batch(self, run_id, *, expected_sequence, checkpoint, records, state="running", stop_reason=None):
        row = self.rows[run_id]
        if row["sequence"] != expected_sequence:
            raise ValueError("stale")
        row.update(sequence=checkpoint["evaluations"], checkpoint=json.loads(json.dumps(checkpoint)),
                   state=state, stop_reason=stop_reason)
        self.records.extend(copy.deepcopy(records))


def setup(max_evaluations=18, retention=None):
    public = PublicInput("abc ab cab abc", "prefix-unit-v1", "preserve")
    cfg = Config(steps=8, restarts=2, order=2, seed=7)
    strategy, evaluator = AnnealingSearch(public, TRAIN, cfg), KeyEvaluator(public, TRAIN, cfg)
    spec = specification(max_evaluations=max_evaluations, retention=retention or {
        "top_k": 3, "reservoir": 2, "full_compact": True}, configuration={
            "execution_binding": fingerprint({"strategy": strategy.identity(),
                "evaluator": evaluator.identity(), "batch_size": 2})})
    return spec, strategy, evaluator


def scientific(summary):
    return [(x["candidate_id"], x["loss"], x["payload"]) for x in summary["top"]]


class RunnerTests(unittest.TestCase):
    def test_budget_retention_parallel_and_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec, search, evaluator = setup()
            store = MemoryRegistry()
            full = ExperimentRunner(store, root).run(spec, search, evaluator, batch_size=2)
            self.assertEqual(full["evaluations"], 18)
            self.assertLessEqual(len(full["top"]), 3)
            self.assertEqual(full["reservoir_retained"], 2)
            self.assertEqual(len(store.records), 18)
            _, search, evaluator = setup()
            parallel = ExperimentRunner(MemoryRegistry(), root).run(spec, search, evaluator,
                batch_size=2, workers=2)
            self.assertEqual(scientific(full), scientific(parallel))
            resumed_store = MemoryRegistry()
            _, search, evaluator = setup()
            runner = ExperimentRunner(resumed_store, root)
            paused = runner.run(spec, search, evaluator, batch_size=2, stop_after_batches=2)
            self.assertEqual(paused["evaluations"], 4)
            _, search, evaluator = setup()
            resumed = runner.run(spec, search, evaluator, batch_size=2, run_id=paused["run_id"])
            self.assertEqual(scientific(full), scientific(resumed))
            self.assertEqual(len(resumed_store.records), 18)
            self.assertEqual(len({r["sequence"] for r in resumed_store.records}), 18)

    def test_changed_bindings_rejected_before_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            spec, search, evaluator = setup()
            store = MemoryRegistry()
            with self.assertRaises(ValueError):
                ExperimentRunner(store, Path(directory)).run(spec, search, evaluator, batch_size=3)
            self.assertFalse(store.rows)

    def test_crash_after_db_commit_recovers_from_db(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            store = MemoryRegistry()
            spec, search, evaluator = setup()
            runner = ExperimentRunner(store, Path(directory))
            from voynich.storage.artifacts import write_json
            def crash(path, value, **kwargs):
                if path.name == "checkpoint.json":
                    raise OSError("simulated disk interruption")
                return write_json(path, value, **kwargs)
            with patch("voynich.experiments.runner.write_json", side_effect=crash), self.assertRaises(OSError):
                runner.run(spec, search, evaluator, batch_size=2)
            run_id = next(iter(store.rows))
            self.assertEqual(store.get(run_id)["sequence"], 2)
            _, search, evaluator = setup()
            resumed = runner.run(spec, search, evaluator, batch_size=2, run_id=run_id)
            self.assertEqual(resumed["evaluations"], 18)
            self.assertEqual(len(store.records), 18)

    def test_storage_threshold_stops_and_frozen_eval_does_not_mutate(self):
        with tempfile.TemporaryDirectory() as directory:
            spec, search, evaluator = setup(retention={"top_k": 100, "reservoir": 100, "max_bytes": 100})
            summary = ExperimentRunner(MemoryRegistry(), Path(directory)).run(spec, search, evaluator, batch_size=2)
            self.assertEqual(summary["stop_reason"], "storage-limit")
            self.assertEqual(summary["top"], [])
            spec, search, evaluator = setup()
            candidate = search.propose(1)[0]
            before = candidate.recipe
            heldout = replace(evaluator, public=PublicInput("ZZZ", "prefix-unit-v1", "preserve"))
            result = heldout(candidate)
            self.assertIsNone(result.loss)
            self.assertEqual(candidate.recipe, before)

    def test_worker_errors_are_bounded_and_persisted(self):
        class BrokenEvaluator:
            def identity(self):
                return {"evaluator": "broken-test", "deterministic": True}
            def __call__(self, candidate):
                raise ArithmeticError("test-error")
        with tempfile.TemporaryDirectory() as directory:
            _, search, _ = setup()
            evaluator = BrokenEvaluator()
            spec = specification(max_evaluations=3, configuration={
                "execution_binding": fingerprint({"strategy": search.identity(),
                    "evaluator": evaluator.identity(), "batch_size": 2})})
            store = MemoryRegistry()
            summary = ExperimentRunner(store, Path(directory)).run(spec, search, evaluator, batch_size=2)
            self.assertEqual(summary["failures"], 3)
            self.assertEqual(summary["error_counts"], {"ArithmeticError": 3})
            self.assertEqual(summary["top"], [])
            self.assertEqual(summary["scientific_verdict"], "not-assessed")

    def test_future_checkpoint_and_changed_spec_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            store = MemoryRegistry()
            spec, search, evaluator = setup()
            runner = ExperimentRunner(store, Path(directory))
            result = runner.run(spec, search, evaluator, batch_size=2, stop_after_batches=1)
            run_id = result["run_id"]
            changed, search, evaluator = setup(max_evaluations=19)
            with self.assertRaises(ValueError):
                runner.run(changed, search, evaluator, batch_size=2, run_id=run_id)
            store.rows[run_id]["checkpoint"]["schema"] = 999
            _, search, evaluator = setup()
            with self.assertRaises(ValueError):
                runner.run(spec, search, evaluator, batch_size=2, run_id=run_id)
