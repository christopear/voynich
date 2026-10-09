"""Compare a regenerated results directory with a committed one, ignoring provenance fields.

Usage: uv run --locked python scripts/compare_results.py NEW_DIR OLD_DIR

JSON files are compared value by value (floats to a relative 1e-9), CSV and
other files byte for byte. Keys that only record provenance (manifests, file
hashes, script/protocol paths, library versions) are ignored, because they
change whenever code moves. Files named *manifest* are skipped. Exit status 1
if anything differs or is missing.
"""
import json
import sys
from pathlib import Path

IGNORE = {"manifest", "sha256", "script", "protocol", "hashes", "inputs_sha256", "python", "numpy", "sklearn"}


def strip(x):
    if isinstance(x, dict):
        return {k: strip(v) for k, v in x.items() if k not in IGNORE}
    if isinstance(x, list):
        return [strip(v) for v in x]
    return x


def diff(a, b, path="", out=None, tol=1e-9):
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}/{k}: only in {'new' if k in a else 'old'}")
            else:
                diff(a[k], b[k], f"{path}/{k}", out, tol)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} vs {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, f"{path}[{i}]", out, tol)
    elif isinstance(a, float) or isinstance(b, float):
        ok = isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) <= tol * max(1, abs(a), abs(b))
        if not ok:
            out.append(f"{path}: {a} vs {b}")
    elif a != b:
        out.append(f"{path}: {str(a)[:60]} vs {str(b)[:60]}")
    return out


def main(new_dir, old_dir):
    new_dir, old_dir = Path(new_dir), Path(old_dir)
    bad = 0
    for old in sorted(p for p in old_dir.iterdir() if p.is_file() and "manifest" not in p.name):
        new = new_dir / old.name
        if not new.exists():
            print(f"MISSING    {old.name}"); bad += 1; continue
        if old.suffix == ".json":
            ds = diff(strip(json.loads(new.read_text())), strip(json.loads(old.read_text())))
        else:
            ds = [] if new.read_bytes() == old.read_bytes() else ["bytes differ"]
        print(("IDENTICAL  " if not ds else "DIFFERS    ") + old.name + ("" if not ds else f"  {len(ds)} diffs, e.g. {ds[:3]}"))
        bad += bool(ds)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
