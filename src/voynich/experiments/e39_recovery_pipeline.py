"""Preregistered grouped-code recovery diagnosis on existing synthetic cases."""
import argparse
from pathlib import Path
from time import monotonic

from voynich.decipher_search.core import normalize, digest
from voynich.evaluation.scorers import recovery_metrics
from voynich.laboratory.manifest import environment, file_hash, fingerprint
from voynich.paths import ROOT
from voynich.search.grouped import GroupedProblem, GroupedEvaluator
from voynich.search.neighborhood import audit, descend
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import read_json, write_json


def cases():
    old = ROOT/'results/grouped_boundary_2026-10-09'
    prior = read_json(ROOT/'results/parser_retention_2026-10-09/evidence.json')
    original = read_json(old/'evidence.json')
    specs = {fingerprint(s): s for s in read_json(old/'specifications.json')}
    for selected in prior['cases']:
        row = next(r for r in original['rows'] if r['id'] == selected['case_id'])
        stage = next(s for s in original['stages'] if s['case_id'] == row['id'])
        tr = next(r for r in specs[stage['spec_id']]['datasets'] if r['role'] == 'training')
        path = ROOT/('data/italian_dante.txt' if tr['source_id'] == 'dante' else
                     f"data/laboratory_sources/{tr['source_id']}_medical.txt")
        if file_hash(path) != tr['raw_hash']:
            raise ValueError('training source changed')
        training = normalize(path.read_text())[tr['start']:tr['stop']]
        if digest(training) != tr['prepared_hash']:
            raise ValueError('training slice changed')
        p = GroupedProblem(tuple(row['spans']), training,
                           tuple(selected['selected']['policy']['prefixes']), row['spacing'])
        winner = selected['selected']['top'][0]
        candidate = Candidate.create(**winner['candidate'])
        replay = GroupedEvaluator(p)(candidate)
        if replay.loss != winner['loss'] or replay.payload != winner['payload']:
            raise ValueError('historical score replay failed')
        yield row, p, candidate, tr


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    paths = ['results/parser_retention_2026-10-09/evidence.json',
             'results/grouped_boundary_2026-10-09/evidence.json',
             'results/grouped_boundary_2026-10-09/specifications.json',
             'docs/protocols/RECOVERY_PIPELINE_2026-10-10.md']
    write_json(output/'manifest.json', dict(environment=environment(ROOT),
               hashes={p: file_hash(ROOT/p) for p in paths}, per_neighborhood_cap=3000,
               total_cap=48000, historical_represented_evaluations=724992))
    results = []
    for row, problem, candidate, training_ref in cases():
        started = monotonic()
        evaluator = GroupedEvaluator(problem)
        blind = audit(evaluator, candidate, problem.units)
        calibration = row['calibration']
        if list(problem.prefixes) != calibration['oracle_prefixes']:
            raise ValueError('oracle parser differs; key comparison invalid')
        oracle = Candidate.create(**{**candidate.data, 'key':
            {i: calibration['oracle_table'][code] for code, i in problem.ids.items()}})
        truth = ''.join(calibration['truth_spans'])
        if evaluator(oracle).payload['plaintext'].replace('\n', '') != truth:
            raise ValueError('oracle round trip failed')
        diagnostic = audit(evaluator, oracle, problem.units)
        for neighborhood in (blind, diagnostic):
            for name in ('center', 'best'):
                r = neighborhood[name]
                r['recovery'] = recovery_metrics(r['payload']['plaintext'].replace('\n', ''), truth)
        result = dict(case_id=row['id'], training_ref=training_ref, returned=blind,
                      oracle=diagnostic, elapsed_seconds=monotonic()-started)
        write_json(output/'cases'/f"{row['id']}.json", result)
        results.append(result)
        print(row['id'], 'missed moves', blind['improving_neighbors'],
              'oracle improving moves', diagnostic['improving_neighbors'], flush=True)
    write_json(output/'evidence.json', dict(cases=results,
               evaluations=sum(r[n]['evaluations'] for r in results for n in ('returned', 'oracle')),
               validation_evaluations=16,
               evidence_label='Synthetic engineering diagnostic; no manuscript recovery'))


def continuation(output):
    output.mkdir(parents=True, exist_ok=False)
    protocol = 'docs/protocols/RECOVERY_PIPELINE_2026-10-10.md'
    write_json(output/'manifest.json', dict(environment=environment(ROOT),
               protocol_hash=file_hash(ROOT/protocol), per_arm_budget=8192,
               historical_represented_evaluations=724992))
    results = []
    for row, problem, candidate, training_ref in cases():
        arms = {}
        for algorithm in ('systematic', 'random'):
            started = monotonic()
            result = descend(GroupedEvaluator(problem), candidate, problem.units,
                             algorithm=algorithm, budget=8192, seed=39001+row['seed'])
            # Truth is consulted only after this arm has selected its final key.
            result['best']['recovery'] = recovery_metrics(
                result['best']['payload']['plaintext'].replace('\n', ''),
                ''.join(row['calibration']['truth_spans']))
            result['elapsed_seconds'] = monotonic()-started
            arms[algorithm] = result
            print(row['id'], algorithm, result['best']['recovery'], flush=True)
        item = dict(case_id=row['id'], training_ref=training_ref, arms=arms)
        write_json(output/'cases'/f"{row['id']}.json", item)
        results.append(item)
    write_json(output/'evidence.json', dict(cases=results, validation_evaluations=8,
               evaluations=sum(a['evaluations'] for r in results for a in r['arms'].values()),
               evidence_label='Development continuation; not fresh blind calibration'))


def verify(output):
    """Replay exported keys and truth metrics without launching another search."""
    diagnosis = {r['case_id']: r for r in read_json(output/'evidence.json')['cases']}
    continued = {r['case_id']: r for r in read_json(output/'continuation/evidence.json')['cases']}
    checked = 0
    for row, problem, _, _ in cases():
        records = [diagnosis[row['id']][arm][position]
                   for arm in ('returned', 'oracle') for position in ('center', 'best')]
        records += [r['best'] for r in continued[row['id']]['arms'].values()]
        for saved in records:
            replay = GroupedEvaluator(problem)(Candidate.create(**saved['candidate']))
            if (replay.payload != saved['payload'] or
                    dict(replay.score.components) != saved['components'] or
                    sum(v for _, v in replay.score.components) != saved['total_bits'] or
                    recovery_metrics(replay.payload['plaintext'].replace('\n', ''),
                                     ''.join(row['calibration']['truth_spans'])) != saved['recovery']):
                raise AssertionError('export replay mismatch')
            checked += 1
    write_json(output/'verification.json', dict(replayed_records=checked,
               historical_start_replays=8, all_exact=True,
               evidence_hashes={p: file_hash(output/p) for p in
                                ('evidence.json', 'continuation/evidence.json')}))
    print('Exactly replayed', checked, 'exported records and 8 historical starts')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/recovery_pipeline_2026-10-10')
    parser.add_argument('--continuation', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.continuation and args.verify:
        parser.error('choose continuation or verification')
    (verify if args.verify else continuation if args.continuation else run)(args.output)


if __name__ == '__main__':
    main()
