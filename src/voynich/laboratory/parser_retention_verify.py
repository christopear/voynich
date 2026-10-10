"""Verify all-survivor runs using the original independent grouped verifier."""
import argparse
import tempfile
from pathlib import Path

from voynich.laboratory.grouped_verify import verify
from voynich.laboratory.manifest import file_hash
from voynich.paths import ROOT
from voynich.storage.artifacts import read_json, write_json


def verify_retention(directory, output):
    previous = ROOT/'results/grouped_boundary_2026-10-09'
    evidence = read_json(directory/'evidence.json')
    if file_hash(previous/'evidence.json') != evidence['plan']['prior_evidence_sha256']:
        raise AssertionError('Historical evidence changed')
    old = read_json(previous/'evidence.json')
    specs = read_json(previous/'specifications.json') + read_json(directory/'new_specifications.json')
    with tempfile.TemporaryDirectory(prefix='voynich-retention-verify-') as temporary:
        folder = Path(temporary)
        write_json(folder/'evidence.json', {**old, 'stages':evidence['stages']})
        write_json(folder/'specifications.json', specs)
        write_json(folder/'environment.json', read_json(directory/'environment.json'))
        return verify(folder, output)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--directory',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();verify_retention(args.directory,args.output)
