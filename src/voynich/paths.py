"""Shared research-workspace paths, independent of the caller's working directory."""
import os
from pathlib import Path


def project_root() -> Path:
    override = os.environ.get("VOYNICH_ROOT")
    if override:
        root = Path(override).expanduser().resolve()
        if not (root / "data").is_dir():
            raise RuntimeError("VOYNICH_ROOT must point to a workspace containing data/")
        return root
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / "data").is_dir():
            return parent
    raise RuntimeError("Research data are external to the package. Set VOYNICH_ROOT to the research checkout.")


ROOT = project_root()
DATA = ROOT / "data"
RESULTS = ROOT / "results"
