"""Preregistered equal-budget greedy versus annealing on exposed stage 40 starts."""
import argparse
from pathlib import Path
from time import monotonic

from voynich.evaluation.scorers import recovery_metrics
from voynich.experiments.e40_fresh_recovery import training_text
from voynich.laboratory.manifest import environment, file_hash
from voynich.paths import ROOT
from voynich.search.grouped import GroupedProblem, GroupedEvaluator
from voynich.search.key_escape import anneal
from voynich.search.neighborhood import descend
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import read_json, write_json

PREVIOUS = ROOT/'results/fresh_recovery_2026-10-10'
PROTOCOL = ROOT/'docs/protocols/KEY_ESCAPE_2026-10-11.md'


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    public = read_json(PREVIOUS/'public_inputs.json')
    write_json(output/'manifest.json', dict(environment=environment(ROOT), protocol_hash=file_hash(PROTOCOL),
               previous_evidence_hash=file_hash(PREVIOUS/'evidence.json'),
               public_inputs_hash=file_hash(PREVIOUS/'public_inputs.json'), budget_per_arm=8192,
               optimization_cap=114688))
    rows = []
    for row in public:
        prior = read_json(PREVIOUS/'search'/f"{row['case_id']}.json")
        if prior['status'] != 'completed':
            continue
        problem = GroupedProblem(tuple(row['spans']), training_text(row),
                                 tuple(prior['selected']['policy']['prefixes']), row['spacing'])
        evaluator = GroupedEvaluator(problem)
        start = Candidate.create(**prior['selected']['best']['candidate'])
        arms = {}
        for method in ('greedy', 'annealing'):
            started = monotonic()
            if method == 'greedy':
                result = descend(evaluator, start, problem.units, algorithm='random',
                                 budget=8192, seed=39001+row['seed'])
                if result['best'] != prior['refined']['best']:
                    raise AssertionError('greedy control does not exactly replay stage 40')
            else:
                result = anneal(evaluator, start, problem.units, budget=8192,
                                seed=39001+row['seed'], acceptance_seed=49001+row['seed'])
            result['elapsed_seconds'] = monotonic()-started
            arms[method] = result
            print(row['case_id'], method, 'complete', flush=True)
        saved = dict(case_id=row['case_id'], arms=arms,
                     prior_search_hash=file_hash(PREVIOUS/'search'/f"{row['case_id']}.json"))
        write_json(output/'search'/f"{row['case_id']}.json", saved)
        rows.append(saved)
    if len(rows) != 7:
        raise AssertionError('unexpected comparison inventory')
    truth = {r['case_id']: ''.join(r['truth_spans']) for r in read_json(PREVIOUS/'fixture_truth.json')}
    assessments = []
    for row in rows:
        metrics = {arm: recovery_metrics(r['best']['payload']['plaintext'].replace('\n', ''), truth[row['case_id']])
                   for arm, r in row['arms'].items()}
        assessments.append(dict(case_id=row['case_id'], metrics=metrics,
            difference=metrics['annealing']['nonspace_edit_accuracy']-metrics['greedy']['nonspace_edit_accuracy']))
    mean = sum(r['difference'] for r in assessments)/len(assessments)
    passes = {arm: sum(r['metrics'][arm]['nonspace_edit_accuracy'] >= .9 for r in assessments)
              for arm in ('greedy', 'annealing')}
    evidence = dict(cases=assessments, mean_difference=mean, passes=passes,
                    gate=mean >= .05 and passes['annealing'] >= passes['greedy']
                         and min(r['difference'] for r in assessments) >= -.1,
                    evaluations=sum(a['evaluations'] for r in rows for a in r['arms'].values()),
                    label='Exposed-development engineering comparison; not fresh calibration')
    write_json(output/'evidence.json', evidence)
    print('RESULT', evidence, flush=True)


def verify(output):
    count = 0
    for row in read_json(PREVIOUS/'public_inputs.json'):
        path = output/'search'/f"{row['case_id']}.json"
        if not path.exists():
            continue
        prior = read_json(PREVIOUS/'search'/f"{row['case_id']}.json")
        evaluator = GroupedEvaluator(GroupedProblem(tuple(row['spans']), training_text(row),
                    tuple(prior['selected']['policy']['prefixes']), row['spacing']))
        for arm in read_json(path)['arms'].values():
            saved = arm['best']
            value = evaluator(Candidate.create(**saved['candidate']))
            if value.payload != saved['payload'] or dict(value.score.components) != saved['components']:
                raise AssertionError('export replay mismatch')
            count += 1
    if count != 14:
        raise AssertionError('missing arm')
    write_json(output/'verification.json', dict(exact_replays=count,
               evidence_hash=file_hash(output/'evidence.json')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/key_escape_2026-10-11')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    (verify if args.verify else run)(args.output)


if __name__ == '__main__':
    main()
