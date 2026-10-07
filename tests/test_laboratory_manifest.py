import json
from pathlib import Path
import tempfile
import unittest
from voynich.laboratory.manifest import (DatasetRef, ExperimentSpec, canonical,
    fingerprint, stream_seed, scope_changes)
from voynich.storage.artifacts import write_json, read_json


def specification(**overrides):
    arguments = dict(family="glyph", method_version="test-v1",
        datasets=(DatasetRef("a", "latin", "a"*64, "b"*64, "development", 0, 10, "n1", "work"),),
        configuration={"spacing": "preserve"}, environment={"test": True}, max_evaluations=10)
    arguments.update(overrides)
    return ExperimentSpec.create(**arguments)


class ManifestTests(unittest.TestCase):
    def test_canonical_and_reject_nonfinite(self):
        self.assertEqual(fingerprint({"b": 1, "a": 2}), fingerprint({"a": 2, "b": 1}))
        for value in (float("nan"), float("inf"), {1: "bad"}):
            with self.assertRaises(ValueError):
                canonical(value)

    def test_immutable_spec_and_scope(self):
        config = {"spacing": "preserve"}
        spec = specification(configuration=config)
        config["spacing"] = "infer"
        self.assertEqual(spec.data["configuration"]["spacing"], "preserve")
        self.assertNotEqual(spec.id, specification(configuration=config).id)
        self.assertEqual(scope_changes(spec.data, specification(configuration=config).data),
                         ["configuration.spacing"])
        data = spec.data
        data["schema"] = 999
        with self.assertRaises(ValueError):
            ExperimentSpec(json.dumps(data))

    def test_overlap_and_independent_streams(self):
        a = DatasetRef("a", "latin", "a"*64, "b"*64, "training", 0, 10, "n1", "work")
        b = DatasetRef("a", "latin", "a"*64, "c"*64, "evaluation", 9, 20, "n1", "work")
        with self.assertRaises(ValueError):
            specification(datasets=(a, b))
        self.assertEqual(stream_seed(1, "page", "key"), stream_seed(1, "page", "key"))
        self.assertNotEqual(stream_seed(1, "page", "key"), stream_seed(1, "page", "choices"))

    def test_atomic_artifact_no_clobber_checksum(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "value.json"
            sha = write_json(path, {"a": 1})
            with self.assertRaises(FileExistsError):
                write_json(path, {"a": 2})
            self.assertEqual(read_json(path, expected_hash=sha), {"a": 1})
            write_json(path, {"a": 2}, replace=True)
            with self.assertRaises(ValueError):
                read_json(path, expected_hash=sha)
            self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_all_scope_axes_change_identity(self):
        from dataclasses import replace
        original = specification()
        source = DatasetRef(**original.data["datasets"][0])
        variations = [
            specification(datasets=(replace(source, language="italian"),)),
            specification(datasets=(replace(source, source_id="different"),)),
            specification(datasets=(replace(source, normalization="n2"),)),
            specification(environment={"solver_version": "different"}),
            specification(max_evaluations=11),
        ]
        self.assertTrue(all(spec.id != original.id for spec in variations))
        self.assertEqual(original.id, specification().id)
