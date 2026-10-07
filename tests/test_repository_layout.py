"""Check package wiring and data discovery after the src-layout migration."""
import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from voynich.cli import experiments
from voynich.paths import ROOT


class RepositoryLayoutTests(unittest.TestCase):
    def test_experiment_modules_import_without_running(self):
        for module in experiments().values():
            imported = importlib.import_module("voynich.experiments." + module)
            self.assertTrue(callable(imported.main), module)

    def test_data_and_document_locations(self):
        self.assertTrue((ROOT / "data/ZL3b-n.txt").is_file())
        self.assertTrue((ROOT / "docs/protocols/COUPLING_TEST_V3_PROTOCOL.md").is_file())

    def test_installed_cli_outside_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ)
            env.pop("PYTHONPATH", None)
            result = subprocess.run([sys.executable, "-m", "voynich", "list"], cwd=directory,
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("26  decipherment_search", result.stdout)
