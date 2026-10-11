"""Post hoc oracle costs for completed stage 40 cases; no additional search."""
import argparse
from pathlib import Path

from voynich.experiments.e40_fresh_recovery import training_text
from voynich.laboratory.manifest import file_hash
from voynich.paths import ROOT
from voynich.search.grouped import GroupedProblem, GroupedEvaluator
from voynich.search.neighborhood import record
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import read_json, write_json


def run(output):
    private = {r['case_id']: r for r in read_json(output/'fixture_truth.json')}
    rows = []
    for public in read_json(output/'public_inputs.json'):
        case = public['case_id']
        result = read_json(output/'search'/f'{case}.json')
        if result['status'] != 'completed':
            continue
        truth = private[case]
        problem = GroupedProblem(tuple(public['spans']), training_text(public),
                                 tuple(truth['prefixes']), public['spacing'])
        candidate = Candidate.create('explicit-codebook-v1', long_prefixes=[],
                    key={code_id: truth['table'][code] for code, code_id in problem.ids.items()})
        value = GroupedEvaluator(problem)(candidate)
        if value.payload['plaintext'].replace('\n', '') != ''.join(truth['truth_spans']):
            raise AssertionError('oracle does not reproduce fixture plaintext')
        oracle = record(candidate, value)
        found = result['refined']['best']
        rows.append(dict(case_id=case, oracle=oracle,
                         found_minus_oracle_bits=found['total_bits']-oracle['total_bits'],
                         components_found_minus_oracle={k: v-oracle['components'][k]
                                                       for k, v in found['components'].items()}))
    write_json(output/'posthoc_oracle.json', dict(cases=rows, evaluations=len(rows),
               status='Post hoc known-answer score comparison; no optimization or gate changes',
               evidence_hash=file_hash(output/'evidence.json'), source_hash=file_hash(Path(__file__))))
    for row in rows:
        print(row['case_id'], 'found minus true key bits', round(row['found_minus_oracle_bits'], 3))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/fresh_recovery_2026-10-10')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
