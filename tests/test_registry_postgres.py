"""Opt-in integration tests. Each test uses a fresh, isolated schema."""
import os
from pathlib import Path
import unittest
import uuid
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from voynich.storage.database import DatabaseSettings, make_engine
from voynich.storage.registry import Registry, DuplicateExperiment
from tests.test_laboratory_manifest import specification

@unittest.skipUnless(os.environ.get("POSTGRES_TEST_URL"), "set POSTGRES_TEST_URL for integration tests")
class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.engine = make_engine(DatabaseSettings.from_env({"POSTGRES_URL": os.environ["POSTGRES_TEST_URL"]}))
        self.schema = "test_lab_" + uuid.uuid4().hex
        self.connection = self.engine.connect()
        self.connection.execute(text(f'CREATE SCHEMA "{self.schema}"'))
        self.connection.execute(text(f'SET search_path TO "{self.schema}"'))
        self.connection.commit()
        cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        cfg.attributes["connection"] = self.connection
        command.upgrade(cfg, "head")
        # Registry uses engine.begin(); bind it to the same search path on every
        # pooled connection through connection options, keeping tests isolated.
        self.connection.close()
        from sqlalchemy import event
        @event.listens_for(self.engine, "checkout")
        def search_path(dbapi, *_):
            old = dbapi.autocommit
            dbapi.autocommit = True
            try:
                with dbapi.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{self.schema}"')
            finally:
                dbapi.autocommit = old
        self.registry = Registry(self.engine)

    def tearDown(self):
        with self.engine.begin() as c:
            c.execute(text(f'DROP SCHEMA "{self.schema}" CASCADE'))
        self.engine.dispose()

    def test_register_rerun_scope_and_atomic_batch(self):
        spec = specification()
        run = self.registry.register(spec, "/tmp/not-written")
        with self.assertRaises(DuplicateExperiment):
            self.registry.register(spec, "/tmp/not-written")
        repeat = self.registry.register(spec, "/tmp/not-written", rerun_reason="replication")
        self.assertNotEqual(run, repeat)
        self.registry.register(specification(max_evaluations=11), "/tmp/not-written")
        self.assertEqual(len(self.registry.list(family="glyph", spec_id=spec.id)), 2)
        record = dict(attempt_id=str(uuid.uuid4()), request_id="a"*64, candidate_id="b"*64, sequence=1)
        self.registry.commit_batch(run, expected_sequence=0, checkpoint={"evaluations": 1},
                                   records=[record])
        with self.assertRaises(ValueError):
            self.registry.commit_batch(run, expected_sequence=0, checkpoint={"evaluations": 1},
                                       records=[record])
        self.assertEqual(self.registry.get(run)["sequence"], 1)
        with self.assertRaises(Exception):
            self.registry.commit_batch(run, expected_sequence=1, checkpoint={"evaluations": 2},
                                       records=[{**record, "sequence": 2}])  # duplicate PK rolls back checkpoint
        self.assertEqual(self.registry.get(run)["sequence"], 1)

    def test_historical_import_no_fabricated_provenance(self):
        path = Path(__file__).resolve().parents[1] / "results/decipher_framework_2026-09-30/latin_glyph_controls.json"
        self.registry.import_pilot(path)
        with self.assertRaises(DuplicateExperiment):
            self.registry.import_pilot(path)
        row = self.registry.list()[0]
        self.assertEqual(row["state"], "completed")
        self.assertTrue(row["manifest"]["unknown"])
        self.assertEqual(row["evidence_status"], "historical-engineering-pilot")

    def test_runner_persists_and_resumes_real_transactions(self):
        import tempfile
        from voynich.experiments.runner import ExperimentRunner
        from tests.test_laboratory_runner import setup
        with tempfile.TemporaryDirectory() as directory:
            spec, search, evaluator = setup()
            runner = ExperimentRunner(self.registry, Path(directory))
            paused = runner.run(spec, search, evaluator, batch_size=2, stop_after_batches=1)
            self.assertEqual(self.registry.get(paused["run_id"])["sequence"], 2)
            _, search, evaluator = setup()
            result = runner.run(spec, search, evaluator, batch_size=2, run_id=paused["run_id"])
            self.assertEqual(result["evaluations"], 18)
            with self.engine.connect() as c:
                count = c.scalar(text("SELECT count(*) FROM lab_attempts"))
            self.assertEqual(count, 18)

    def test_concurrent_duplicate_and_future_migration(self):
        from concurrent.futures import ThreadPoolExecutor
        spec = specification()
        def register(_):
            try:
                return self.registry.register(spec, "/tmp/not-written")
            except DuplicateExperiment:
                return "duplicate"
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(register, range(2)))
        self.assertEqual(results.count("duplicate"), 1)
        self.assertEqual(len(self.registry.list()), 1)
