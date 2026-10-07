"""Table declarations only: imports never create tables or connect."""
from sqlalchemy import (MetaData, Table, Column, String, Integer, BigInteger, JSON,
                        ForeignKey, UniqueConstraint, CheckConstraint, DateTime, func)

metadata = MetaData()
specifications = Table("lab_specifications", metadata,
    Column("id", String(64), primary_key=True),
    Column("family", String, nullable=False, index=True),
    Column("manifest", JSON, nullable=False))
runs = Table("lab_runs", metadata,
    Column("id", String(36), primary_key=True),
    Column("spec_id", ForeignKey("lab_specifications.id"), nullable=False, index=True),
    Column("state", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("reason", String),
    Column("stop_reason", String),
    Column("artifact_dir", String, nullable=False),
    Column("evidence_status", String, nullable=False),
    Column("sequence", Integer, nullable=False, default=0),
    Column("checkpoint", JSON),
    Column("checkpoint_hash", String(64)),
    CheckConstraint("state IN ('created','running','completed','stopped','failed')"))
attempts = Table("lab_attempts", metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", ForeignKey("lab_runs.id"), nullable=False, index=True),
    Column("request_id", String(64), nullable=False),
    Column("candidate_id", String(64), nullable=False, index=True),
    Column("sequence", BigInteger, nullable=False),
    Column("record", JSON, nullable=False),
    UniqueConstraint("run_id", "sequence", name="uq_lab_attempt_sequence"))
