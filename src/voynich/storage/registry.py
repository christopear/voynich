"""PostgreSQL registry with serialized duplicate checks and atomic batch commits."""
from pathlib import Path
import uuid
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from voynich.laboratory.manifest import ExperimentSpec, fingerprint
from .schema import specifications, runs, attempts


class DuplicateExperiment(ValueError):
    pass


class Registry:
    def __init__(self, engine):
        self.engine = engine

    def register(self, spec: ExperimentSpec, artifact_dir: str, *,
                 rerun_reason: str | None = None, evidence_status: str = "execution-only") -> str:
        return self._register(spec.id, spec.data, artifact_dir, rerun_reason, evidence_status)

    def _register(self, spec_id, manifest, artifact_dir, rerun_reason, evidence_status,
                  state="created"):
        run_id = str(uuid.uuid4())
        with self.engine.begin() as conn:
            # Lock even before the first specification exists: concurrent first runs
            # cannot both pass the duplicate check.
            lock = int(spec_id[:15], 16)
            conn.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})
            conn.execute(insert(specifications).values(id=spec_id, family=manifest["family"],
                manifest=manifest).on_conflict_do_nothing(index_elements=["id"]))
            previous = conn.scalar(select(runs.c.id).where(runs.c.spec_id == spec_id).limit(1))
            if previous and not (rerun_reason and rerun_reason.strip()):
                raise DuplicateExperiment(f"Specification already has run {previous}; record a rerun reason")
            conn.execute(runs.insert().values(id=run_id, spec_id=spec_id, state=state,
                reason=rerun_reason, artifact_dir=artifact_dir, evidence_status=evidence_status, sequence=0))
        return run_id

    def list(self, *, family=None, spec_id=None):
        query = select(*(c for c in runs.c if c.name not in {"checkpoint", "checkpoint_hash"}),
                       specifications.c.family, specifications.c.manifest).join(
            specifications, runs.c.spec_id == specifications.c.id)
        if family:
            query = query.where(specifications.c.family == family)
        if spec_id:
            query = query.where(runs.c.spec_id == spec_id)
        with self.engine.connect() as conn:
            return [dict(row) for row in conn.execute(query.order_by(runs.c.id)).mappings()]

    def get(self, run_id):
        with self.engine.connect() as conn:
            row = conn.execute(select(runs).where(runs.c.id == run_id)).mappings().first()
        if row is None:
            raise KeyError("unknown run")
        if row["checkpoint"] is not None and fingerprint(row["checkpoint"]) != row["checkpoint_hash"]:
            raise ValueError("database checkpoint checksum mismatch")
        return dict(row)

    def commit_batch(self, run_id, *, expected_sequence, checkpoint, records,
                     state="running", stop_reason=None):
        """Checkpoint and rows share a transaction; replay never double-counts."""
        sequence = checkpoint["evaluations"]
        if type(sequence) is not int or sequence < expected_sequence or state not in {"running", "completed", "stopped", "failed"}:
            raise ValueError("invalid batch state/sequence")
        if records and [r["sequence"] for r in records] != list(range(expected_sequence + 1, sequence + 1)):
            raise ValueError("compact records must cover exactly the completed batch")
        with self.engine.begin() as conn:
            current = conn.execute(select(runs).where(runs.c.id == run_id).with_for_update()).mappings().one()
            if current["state"] == "completed":
                raise ValueError("completed run history is immutable")
            if current["sequence"] != expected_sequence:
                raise ValueError("stale checkpoint or concurrent coordinator")
            for record in records:
                conn.execute(attempts.insert().values(
                    id=record["attempt_id"], run_id=run_id,
                    request_id=record["request_id"], candidate_id=record["candidate_id"],
                    sequence=record["sequence"], record=record))
            conn.execute(runs.update().where(runs.c.id == run_id).values(
                sequence=sequence, checkpoint=checkpoint, checkpoint_hash=fingerprint(checkpoint),
                state=state, stop_reason=stop_reason))


    def import_pilot(self, path: Path):
        import json
        from voynich.laboratory.manifest import file_hash
        data = json.loads(path.read_text())
        if not {"source", "config", "provenance", "cases"} <= data.keys():
            raise ValueError("not a recognized framework pilot")
        manifest = {"schema": "legacy-pilot-v1", "family": data["config"]["family"],
                    "artifact_sha256": file_hash(path), "source": data["source"],
                    "configuration": data["config"], "environment": data["provenance"],
                    "split": data.get("split"), "interpretation": data.get("interpretation"),
                    "unknown": ["exact source spans", "dependency lock", "predeclared threshold",
                                "work genre/date", "dirty source state"],
                    "limitations": "Historical engineering pilot; not calibrated family rejection."}
        return self._register(fingerprint(manifest), manifest, str(path.resolve()), None,
                              "historical-engineering-pilot", "completed")
