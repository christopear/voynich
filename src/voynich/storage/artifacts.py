"""Atomic JSON artifacts. Content hashes identify payloads, not recipes."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
from voynich.laboratory.manifest import canonical


def write_json(path: Path, value, *, replace: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical(value).encode()
    fd, name = tempfile.mkstemp(prefix="." + path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(name, path)
        else:
            # Atomic no-clobber publication, including competing processes.
            os.link(name, path)
            os.unlink(name)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path, *, expected_hash: str | None = None):
    payload = path.read_bytes()
    if expected_hash and hashlib.sha256(payload).hexdigest() != expected_hash:
        raise ValueError("artifact checksum mismatch")
    return json.loads(payload)
