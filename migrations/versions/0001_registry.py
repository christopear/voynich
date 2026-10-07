"""Initial registry, runs and compact attempt store."""
from alembic import op
import sqlalchemy as sa
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("lab_specifications",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("family", sa.String(), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False))
    op.create_index("ix_lab_specifications_family", "lab_specifications", ["family"])
    op.create_table("lab_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("spec_id", sa.String(64), sa.ForeignKey("lab_specifications.id"), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reason", sa.String()),
        sa.Column("stop_reason", sa.String()),
        sa.Column("artifact_dir", sa.String(), nullable=False),
        sa.Column("evidence_status", sa.String(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("checkpoint", sa.JSON()),
        sa.Column("checkpoint_hash", sa.String(64)),
        sa.CheckConstraint("state IN ('created','running','completed','stopped','failed')"))
    op.create_index("ix_lab_runs_spec_id", "lab_runs", ["spec_id"])
    op.create_table("lab_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("lab_runs.id"), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("candidate_id", sa.String(64), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("record", sa.JSON(), nullable=False),
        sa.UniqueConstraint("run_id", "sequence", name="uq_lab_attempt_sequence"))
    op.create_index("ix_lab_attempts_run_id", "lab_attempts", ["run_id"])
    op.create_index("ix_lab_attempts_candidate_id", "lab_attempts", ["candidate_id"])

def downgrade():
    # Destructive downgrades must be explicitly designed if ever needed.
    raise NotImplementedError("use a forward migration; research history is not dropped")
