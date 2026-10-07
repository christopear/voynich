"""Versioned, immutable specifications and content-addressed provenance."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import platform
import random
import subprocess
from typing import Any

SCHEMA = 1


def canonical(value: Any) -> str:
    def validate(x):
        if isinstance(x, dict):
            if any(not isinstance(k, str) for k in x):
                raise ValueError("JSON object keys must be strings")
            for v in x.values():
                validate(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                validate(v)
        elif x is not None and type(x) not in (str, int, float, bool):
            raise ValueError("not a JSON value")
    validate(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stream_seed(master: int, identity: str, purpose: str) -> int:
    return int(fingerprint(["sha256-stream-v1", master, identity, purpose])[:16], 16)


@dataclass(frozen=True)
class DatasetRef:
    source_id: str
    language: str
    raw_hash: str
    prepared_hash: str
    role: str
    start: int
    stop: int
    normalization: str
    work: str
    uri: str | None = None
    genre: str | None = None
    date: str | None = None
    encoding: str = "utf-8"

    def __post_init__(self):
        if self.role not in {"training", "development", "evaluation", "truth"}:
            raise ValueError("unknown dataset role")
        if not all((self.source_id, self.language, self.work, self.normalization)):
            raise ValueError("dataset provenance is required")
        if type(self.start) is not int or type(self.stop) is not int or not 0 <= self.start < self.stop:
            raise ValueError("invalid source span")
        for value in (self.raw_hash, self.prepared_hash):
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("expected a SHA-256 content hash")


def validate_splits(datasets: tuple[DatasetRef, ...]):
    public = [d for d in datasets if d.role != "truth"]
    for i, a in enumerate(public):
        for b in public[i + 1:]:
            if a.role == b.role:
                continue
            if a.prepared_hash == b.prepared_hash:
                raise ValueError("identical prepared content across dataset roles")
            same_source = a.source_id == b.source_id or a.raw_hash == b.raw_hash
            if same_source and max(a.start, b.start) < min(a.stop, b.stop):
                raise ValueError("overlapping source spans across dataset roles")


@dataclass(frozen=True)
class ExperimentSpec:
    """Store canonical JSON internally to prevent mutation after fingerprinting."""
    payload: str

    @classmethod
    def create(cls, *, family: str, method_version: str, datasets: tuple[DatasetRef, ...],
               configuration: dict, environment: dict, max_evaluations: int,
               seed: int = 0, retention: dict | None = None) -> "ExperimentSpec":
        validate_splits(datasets)
        return cls(canonical(dict(schema=SCHEMA, family=family, method_version=method_version,
                                  datasets=[asdict(d) for d in datasets], configuration=configuration,
                                  environment=environment, max_evaluations=max_evaluations,
                                  seed=seed, retention=retention or {"top_k": 100, "reservoir": 100})))

    def __post_init__(self):
        data = json.loads(self.payload)
        if data.get("schema") != SCHEMA:
            raise ValueError("unsupported specification schema")
        required = {"schema", "family", "method_version", "datasets", "configuration",
                    "environment", "max_evaluations", "seed", "retention"}
        if set(data) != required:
            raise ValueError("invalid specification fields")
        if not data["family"] or not data["method_version"]:
            raise ValueError("method identity is required")
        if type(data["max_evaluations"]) is not int or data["max_evaluations"] < 1:
            raise ValueError("positive evaluation budget required")
        if type(data["seed"]) is not int:
            raise ValueError("integer seed required")
        datasets = tuple(DatasetRef(**d) for d in data["datasets"])
        if not datasets:
            raise ValueError("at least one dataset is required")
        validate_splits(datasets)
        if not isinstance(data["configuration"], dict) or not isinstance(data["environment"], dict):
            raise ValueError("configuration/environment must be objects")
        retention = data["retention"]
        if set(retention) - {"top_k", "reservoir", "full_compact", "max_bytes"}:
            raise ValueError("unknown retention setting")
        for key in ("top_k", "reservoir"):
            if type(retention.get(key)) is not int or retention[key] < 0:
                raise ValueError("nonnegative retention limits required")
        if "max_bytes" in retention and (type(retention["max_bytes"]) is not int or retention["max_bytes"] < 1):
            raise ValueError("positive storage budget required")
        if "full_compact" in retention and type(retention["full_compact"]) is not bool:
            raise ValueError("full_compact must be boolean")
        object.__setattr__(self, "payload", canonical(data))

    @property
    def data(self) -> dict:
        return json.loads(self.payload)

    @property
    def id(self) -> str:
        return fingerprint(self.data)


def environment(root: Path) -> dict:
    """Hash code and the lock file, including dirty content; never inspect .env."""
    def git(*args):
        try:
            return subprocess.check_output(["git", *args], cwd=root, text=True,
                                           stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    sources = {str(p.relative_to(root)): file_hash(p) for p in sorted((root / "src").rglob("*.py"))}
    status = git("status", "--porcelain")
    return {"git_commit": git("rev-parse", "HEAD"), "git_dirty": None if status is None else bool(status),
            "source_hashes": sources, "lock_hash": file_hash(root / "uv.lock"),
            "python": platform.python_version(), "rng": f"python-random-state-{random.Random().getstate()[0]}",
            "seed_derivation": "sha256-stream-v1"}


def scope_changes(previous: dict, proposed: dict) -> list[str]:
    """Return exact changed paths, without implying scientific equivalence."""
    changes = []
    def walk(a, b, path):
        if isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(a.keys() | b.keys()):
                if key not in a or key not in b:
                    changes.append(f"{path}.{key}".strip("."))
                else:
                    walk(a[key], b[key], f"{path}.{key}".strip("."))
        elif a != b:
            changes.append(path)
    walk(previous, proposed, "")
    return changes
