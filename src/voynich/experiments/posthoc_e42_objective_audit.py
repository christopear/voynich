"""Post hoc true-key score diagnostics; no search or changes to stage 42 gates."""
import argparse
from pathlib import Path

from voynich.evaluation.scorers import recovery_metrics
from voynich.experiments.e42_recovery_reliability import SEEDS, METHODS, training_text
from voynich.laboratory.manifest import file_hash
from voynich.paths import ROOT
from voynich.search.grouped import GroupedProblem, GroupedEvaluator
from voynich.search.neighborhood import record
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import read_json, write_json


def run(output):
    private = {r['case_id']: r for r in read_json(output/'fixture_truth.json')}
    public = read_json(output/'public_inputs.json')
    oracle_rows, comparisons = [], []
    for row in public:
        case, truth = row['case_id'], private[row['case_id']]
        problem = GroupedProblem(tuple(row['spans']), training_text(row), tuple(truth['prefixes']), row['spacing'])
        candidate = Candidate.create('explicit-codebook-v1', long_prefixes=[],
                    key={i: truth['table'][c] for c, i in problem.ids.items()})
        value = GroupedEvaluator(problem)(candidate)
        reference = ''.join(truth['truth_spans'])
        if value.payload['plaintext'].replace('\n', '') != reference:
            raise AssertionError('true key fails round trip')
        oracle = record(candidate, value)
        oracle_rows.append(dict(case_id=case, oracle=oracle))
        for seed in SEEDS:
            trial = read_json(output/'trials'/f'{case}-{seed}.json')
            if trial['status'] != 'completed':
                continue
            for method in METHODS:
                found = trial['arms'][method]['best']
                accuracy = recovery_metrics(found['payload']['plaintext'].replace('\n', ''), reference)
                gap = found['total_bits']-oracle['total_bits']
                comparisons.append(dict(case_id=case, seed=seed, method=method, recovery=accuracy,
                    found_minus_true_bits=gap, correct_parser=trial['selected']['policy']['prefixes'] == truth['prefixes'],
                    known_better_true_key=gap > 1e-9,
                    wrong_output_outscores_truth=accuracy['edit_accuracy'] < 1 and gap < -1e-9))
    summaries = {}
    for method in METHODS:
        rows = [r for r in comparisons if r['method'] == method]
        failed = [r for r in rows if r['recovery']['nonspace_edit_accuracy'] < .9]
        summaries[method] = dict(below_90=len(failed),
            below_90_with_better_true_key=sum(r['known_better_true_key'] for r in failed),
            below_90_outscoring_truth=sum(r['wrong_output_outscores_truth'] for r in failed),
            wrong_outputs_outscoring_truth=sum(r['wrong_output_outscores_truth'] for r in rows))
    write_json(output/'posthoc_objective.json', dict(oracle_evaluations=len(oracle_rows),
               oracle_keys=oracle_rows, comparisons=comparisons, summaries=summaries,
               label='Post hoc diagnostic only; not method selection or new calibration',
               evidence_hash=file_hash(output/'evidence.json'), source_hash=file_hash(Path(__file__))))
    print(summaries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/recovery_reliability_2026-10-11')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
