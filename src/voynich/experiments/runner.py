"""Single-coordinator execution with bounded retention and durable checkpoints."""
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import multiprocessing
from pathlib import Path
import random
import time
import uuid

from voynich.evaluation.outcomes import ScoreReport
from voynich.evaluation.scorers import Evaluation
from voynich.laboratory.manifest import canonical, fingerprint, stream_seed
from voynich.search.strategies import tuples
from voynich.storage.artifacts import write_json


def execute(evaluator, candidate):
    try:
        return evaluator(candidate)
    except Exception as exc:
        # Bounded diagnostics without persisting potentially sensitive exception data.
        return Evaluation(ScoreReport("execution-error-v1", (), 1, 0, False), {},
                          "error", type(exc).__name__)


def worker(arguments):
    return execute(*arguments)


class ExperimentRunner:
    def __init__(self, registry, artifact_root: Path):
        self.registry, self.artifact_root = registry, artifact_root

    def run(self, spec, strategy, evaluator, *, workers=1, batch_size=16,
            run_id=None, rerun_reason=None, max_seconds=None, stop_after_batches=None):
        if workers < 1 or not 1 <= batch_size <= 1000:
            raise ValueError("positive workers and batch size 1..1000 required")
        if max_seconds is not None and max_seconds <= 0:
            raise ValueError("time budget must be positive")
        settings = spec.data
        binding = fingerprint({"strategy": strategy.identity(), "evaluator": evaluator.identity(),
                               "batch_size": batch_size})
        if evaluator.identity().get("deterministic") is not True:
            raise NotImplementedError("stochastic evaluation replicates need an explicit replication strategy")
        if settings["configuration"].get("max_seconds") != max_seconds:
            raise ValueError("time budget differs from the specification")
        expected = settings["configuration"].get("execution_binding")
        if expected != binding:
            raise ValueError("specification does not bind these inputs, scorer and strategy")
        checkpoint = None
        initial_strategy = strategy.snapshot()
        evaluator_identity = evaluator.identity()
        if run_id is None:
            # Each run receives its own directory; registration is the sole source
            # of identity. A filesystem failure leaves a recoverable created run.
            run_id = self.registry.register(spec, str(self.artifact_root), rerun_reason=rerun_reason)
        else:
            row = self.registry.get(run_id)
            if row["spec_id"] != spec.id:
                raise ValueError("resume specification differs; create a new linked run")
            if row["state"] == "completed":
                raise ValueError("completed runs cannot be resumed")
            if Path(row["artifact_dir"]).resolve() != self.artifact_root.resolve():
                raise ValueError("resume artifact root differs")
            checkpoint = row["checkpoint"]
        directory = self.artifact_root / run_id
        directory.mkdir(parents=True, exist_ok=True)
        if not (directory / "manifest.json").exists():
            write_json(directory / "manifest.json", settings)
        else:
            from voynich.storage.artifacts import read_json
            if read_json(directory / "manifest.json") != settings:
                raise ValueError("stored manifest differs")
        rng = random.Random(stream_seed(settings["seed"], spec.id, "reservoir"))
        if checkpoint:
            if checkpoint.get("schema") != 1 or checkpoint["binding"] != binding:
                raise ValueError("incompatible checkpoint")
            strategy.restore(checkpoint["strategy"])
            rng.setstate(tuples(checkpoint["reservoir_rng"]))
            count, failed = checkpoint["evaluations"], checkpoint["failures"]
            top, reservoir = checkpoint["top"], checkpoint["reservoir"]
            elapsed_before = checkpoint.get("elapsed_seconds", 0)
            error_counts = checkpoint.get("error_counts", {})
        else:
            count = failed = 0
            top, reservoir = [], []
            elapsed_before = 0
            error_counts = {}
        retention = settings["retention"]
        started, batches = time.monotonic(), 0
        pool = ProcessPoolExecutor(workers, mp_context=multiprocessing.get_context("spawn")) if workers > 1 else None
        reason, state = "evaluation-limit", "stopped"
        try:
            while count < settings["max_evaluations"]:
                if max_seconds is not None and elapsed_before + time.monotonic() - started >= max_seconds:
                    reason = "time-limit"
                    break
                if stop_after_batches is not None and batches >= stop_after_batches:
                    reason = "requested-pause"
                    break
                candidates = strategy.propose(min(batch_size, settings["max_evaluations"] - count))
                if not candidates:
                    reason, state = "exhaustive-completion", "completed"
                    break
                values = list(pool.map(worker, ((evaluator, c) for c in candidates))) if pool else [
                    execute(evaluator, c) for c in candidates]
                records, previous = [], count
                for candidate, value in zip(candidates, values):
                    count += 1
                    failed += value.status == "error"
                    if value.error:
                        label = value.error if value.error in error_counts or len(error_counts) < 32 else "other"
                        error_counts[label] = error_counts.get(label, 0) + 1
                    record = {"attempt_id": str(uuid.uuid4()), "candidate_id": candidate.id,
                        "request_id": fingerprint({"candidate": candidate.id,
                            "evaluator": evaluator_identity, "spec": spec.id, "replicate": 0}),
                        "sequence": count, "status": value.status, "score": asdict(value.score),
                        "loss": value.loss, "error": value.error, "replay": "summary-only"}
                    retained = {**record, "replay": "exact-payload", "candidate": candidate.data,
                                "payload": value.payload}
                    if value.loss is not None and retention["top_k"]:
                        existing = {x["candidate_id"]: x for x in top}
                        existing[candidate.id] = retained
                        top = sorted(existing.values(), key=lambda x: (x["loss"], x["candidate_id"]))[:retention["top_k"]]
                    capacity = retention["reservoir"]
                    if len(reservoir) < capacity:
                        reservoir.append(retained)
                    elif capacity:
                        index = rng.randrange(count)
                        if index < capacity:
                            reservoir[index] = retained
                    if retention.get("full_compact", False):
                        records.append(record)
                strategy.observe(values)
                checkpoint = self._checkpoint(binding, strategy, rng, count, failed, top, reservoir,
                    elapsed_before + time.monotonic() - started)
                checkpoint["error_counts"] = error_counts
                if retention.get("max_bytes") and len(canonical(checkpoint).encode()) > retention["max_bytes"]:
                    # Preserve the strategy for replay; stop without storing oversized
                    # optional artifacts. The strategy state itself is irreducible.
                    top, reservoir = [], []
                    checkpoint["top"], checkpoint["reservoir"] = [], []
                    reason = "storage-limit"
                self.registry.commit_batch(run_id, expected_sequence=previous,
                    checkpoint=checkpoint, records=records)
                write_json(directory / "checkpoint.json", checkpoint, replace=True)
                batches += 1
                if reason == "storage-limit":
                    break
            checkpoint = self._checkpoint(binding, strategy, rng, count, failed, top, reservoir,
                elapsed_before + time.monotonic() - started)
            checkpoint["error_counts"] = error_counts
            self.registry.commit_batch(run_id, expected_sequence=count, checkpoint=checkpoint,
                                       records=[], state=state, stop_reason=reason)
            write_json(directory / "checkpoint.json", checkpoint, replace=True)
            summary = {"schema": 1, "run_id": run_id, "spec_id": spec.id, "state": state,
                       "stop_reason": reason, "evaluations": count, "failures": failed,
                       "top": top, "reservoir_retained": len(reservoir), "error_counts": error_counts,
                       "proposals": count, "cache_hits": 0, "unique_candidates": None,
                       "scientific_verdict": "not-assessed",
                       "strategy_diagnostics": strategy.diagnostics() if hasattr(strategy, "diagnostics") else {}}
            write_json(directory / "summary.json", summary, replace=True)
            return summary
        except BaseException as exc:
            # Database is authoritative even when an artifact mirror write failed.
            durable = self.registry.get(run_id)
            saved = durable["checkpoint"]
            if saved is None:
                strategy.restore(initial_strategy)
                saved = self._checkpoint(binding, strategy, random.Random(
                    stream_seed(settings["seed"], spec.id, "reservoir")), 0, 0, [], [], 0)
            try:
                self.registry.commit_batch(run_id, expected_sequence=durable["sequence"],
                    checkpoint=saved, records=[], state="stopped" if isinstance(exc, KeyboardInterrupt) else "failed",
                    stop_reason="user-cancellation" if isinstance(exc, KeyboardInterrupt) else "infrastructure-error")
            except Exception:
                pass  # Preserve the original exception if PostgreSQL itself is down.
            raise
        finally:
            if pool:
                pool.shutdown(cancel_futures=True)

    @staticmethod
    def _checkpoint(binding, strategy, rng, count, failed, top, reservoir, elapsed):
        return {"schema": 1, "binding": binding, "strategy": strategy.snapshot(),
                "reservoir_rng": rng.getstate(), "evaluations": count, "failures": failed,
                "top": top, "reservoir": reservoir, "elapsed_seconds": elapsed}
