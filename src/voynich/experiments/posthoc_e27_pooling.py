"""Post hoc audit of first-occurrence tie leakage; does not replace frozen results."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from voynich.experiments.e27_unit_association import association, dump, sha
from voynich.paths import ROOT


def pool(tokens, seed):
    counts = Counter(tokens)
    key = lambda t: (-counts[t], hashlib.sha256(f'{seed}:{t}'.encode()).hexdigest())
    keep = set(sorted(counts, key=key)[:200])
    return [(0, t) if t in keep else (1, '') for t in tokens]


def run(source, output):
    output.mkdir(parents=True, exist_ok=False)
    evidence = json.loads((source/'evidence.json').read_text())
    slots = json.loads((source/'manuscript_slots.json').read_text())
    results = []
    for row in evidence['results']:
        if row['kind'] not in {'control', 'manuscript'}:
            continue
        rows = slots['join' if row['id'] == 'voynich-join' else 'split']
        corrected = []
        for tie_seed in (7, 19, 31):
            tokens = pool(row['tokens'], tie_seed)
            corrected.append(dict(tie_seed=tie_seed,
                section=association(tokens, rows), roles=association(tokens, rows, 'roles')))
        results.append(dict(id=row['id'], first_occurrence=row['metrics']['top200_section'],
                            all_type=row['metrics']['all_section'], page_blind_ties=corrected))
    rows = slots['split']
    unique = [str(i) for i in range(len(rows))]
    diagnostic = dict(first_occurrence=association(unique, rows, cap=200),
        all_type=association(unique, rows),
        page_blind=[association(pool(unique, seed), rows) for seed in (7, 19, 31)])
    result = dict(status='post hoc, motivated by shuffled-glyph control', results=results,
        singleton_diagnostic=diagnostic, source_sha256=sha(source/'evidence.json'), code_sha256=sha(Path(__file__)))
    dump(output/'evidence.json', result)
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,default=ROOT/'results/unit_association_2026-10-09')
    ap.add_argument('--output',type=Path,default=ROOT/'results/unit_association_pooling_audit_2026-10-09')
    args=ap.parse_args();run(args.source,args.output)


if __name__ == '__main__':
    main()
