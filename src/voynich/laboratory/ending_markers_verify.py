"""Rerun stage 37 from source and compare every stored number."""
import argparse
import json
from pathlib import Path
import tempfile

from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e37_ending_markers import run
from voynich.paths import ROOT


def verify(folder):
    read = lambda base, name: json.loads((base/name).read_text())
    for path, digest in read(folder, 'manifest.json')['hashes'].items():
        assert sha(ROOT/path) == digest, path
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp)/'rerun'
        run(fresh)
        for name in ('evidence.json', 'calibration.json'):
            assert read(fresh, name) == read(folder, name), name
    return dict(rerun_identical=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'results/ending_markers_2026-10-10')
    folder = parser.parse_args().directory
    result = verify(folder)
    print(json.dumps(result))
    (folder/'verification.json').write_text(json.dumps(dict(result, passed=True))+'\n')


if __name__ == '__main__':
    main()
