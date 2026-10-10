"""Independent multi-seed calibration of greedy, annealing and portfolio recovery."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import string
import textwrap
from time import monotonic

from voynich.ciphers.models import CipherKey
from voynich.ciphers.units import UnitCipher
from voynich.decipher_search.core import normalize, digest
from voynich.evaluation.scorers import recovery_metrics, model
from voynich.experiments.e40_fresh_recovery import SOURCES, training_text, intervals_overlap
from voynich.laboratory.grouped_boundary import fixture
from voynich.laboratory.manifest import environment, file_hash
from voynich.paths import ROOT
from voynich.search.grouped import GroupedProblem, GroupedEvaluator, screen_policies, parse_span, frozen_decode
from voynich.search.grouped_pipeline import beam
from voynich.search.key_escape import anneal
from voynich.search.neighborhood import descend
from voynich.search.portfolio import portfolio, stability
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import read_json, write_json

PROTOCOL = ROOT/'docs/protocols/RECOVERY_RELIABILITY_2026-10-11.md'
PREVIOUS = ROOT/'results/fresh_recovery_2026-10-10'
SEEDS = (101, 202, 303)
METHODS = ('greedy', 'annealing', 'portfolio')


def prepare(output):
    texts = {k: normalize(p.read_text()) for k, p in SOURCES.items()}
    old_truth = read_json(PREVIOUS/'fixture_truth.json')
    old_public = read_json(PREVIOUS/'public_inputs.json')
    public, private = [], []
    for language, target, trainer in (('latin', 'pliny', 'celsus'), ('italian', 'dante', 'dante')):
        text = texts[target]
        ref = next(r['training_ref'] for r in old_public if r['language'] == language)
        training_text(dict(training_ref=ref))
        starts = [int(f*len(text)) for f in (.85, .90)]
        ranges = [(s, s+350) for s in starts] + [(s+1000, s+1350) for s in starts]
        forbidden = [(int(.7*len(text)), int(.7*len(text))+350)]
        for old in old_truth:
            if old['target_source'] == target:
                forbidden.extend([(old['start'], old['stop']), (old['transfer_start'], old['transfer_stop'])])
        if trainer == target:
            forbidden.append((ref['start'], ref['stop']))
        if any(b > len(text) for a, b in ranges) or any(intervals_overlap(r, other)
                for i, r in enumerate(ranges) for other in ranges[i+1:]+forbidden):
            raise ValueError('overlapping or truncated new passages')
        for start, key_seed in zip(starts, (59, 71)):
            plain, transfer_plain = text[start:start+350].strip(), text[start+1000:start+1350].strip()
            for spacing in ('preserve', 'encoded'):
                case = f'{language}-{spacing}-{key_seed}'
                spans, truth, table, prefixes = fixture(plain, spacing, key_seed)
                method = UnitCipher('groups', homophones=2, lengths='variable', spacing=spacing,
                                    alphabet=string.ascii_uppercase[:16])
                key = CipherKey(method.method_id, tuple(table.items()))
                transfer_truth = textwrap.wrap(transfer_plain, 50, break_long_words=False, break_on_hyphens=False)
                transfer = []
                for i, line in enumerate(transfer_truth):
                    encoded, _ = method.encrypt_text(line, key, seed=240001+key_seed+i)
                    if spacing == 'encoded':
                        encoded = ' '.join(encoded[j:j+5] for j in range(0, len(encoded), 5))
                    transfer.append(encoded)
                if [''.join(' ' if c == ' ' else table[c] for c in parse_span(s, prefixes, spacing))
                        for s in transfer] != transfer_truth:
                    raise AssertionError('transfer round trip failed')
                public.append(dict(case_id=case, language=language, spacing=spacing, key_seed=key_seed,
                                   spans=spans, training_ref=ref))
                private.append(dict(case_id=case, truth_spans=truth, table=table, prefixes=prefixes,
                    target_source=target, raw_hash=file_hash(SOURCES[target]), start=start, stop=start+350,
                    prepared_hash=digest(plain), transfer_start=start+1000, transfer_stop=start+1350,
                    transfer_prepared_hash=digest(transfer_plain), transfer_spans=transfer, transfer_truth=transfer_truth))
    write_json(output/'public_inputs.json', public)
    write_json(output/'fixture_truth.json', private)
    return public


def solve(task):
    row, seed, directory = task
    output = Path(directory)
    started = monotonic()
    train = training_text(row)
    policies = sorted(screen_policies(row['spans'], train, row['spacing'])['survivors'], key=lambda p: p['prefixes'])
    result = dict(case_id=row['case_id'], search_seed=seed, structural_policies=policies,
                  policies=[], arms={}, evaluations=0)
    if not policies or len(policies) > 64:
        result['status'] = 'no_parsers' if not policies else 'parser_budget_cap'
    else:
        for i, policy in enumerate(policies):
            problem = GroupedProblem(tuple(row['spans']), train, tuple(policy['prefixes']), row['spacing'])
            result['policies'].append(dict(policy=policy, **beam(problem, seed)))
            if (i+1) % 10 == 0:
                print(row['case_id'], seed, 'parsers', i+1, '/', len(policies), flush=True)
        selected = min(result['policies'], key=lambda w: (w['loss'], w['policy']['prefixes'], w['candidate_id']))
        result['selected'] = selected
        problem = GroupedProblem(tuple(row['spans']), train, tuple(selected['policy']['prefixes']), row['spacing'])
        evaluator = GroupedEvaluator(problem)
        candidate = Candidate.create(**selected['best']['candidate'])
        result['arms']['greedy'] = descend(evaluator, candidate, problem.units, algorithm='random', budget=8192, seed=39001+seed)
        result['arms']['annealing'] = anneal(evaluator, candidate, problem.units, seed=39001+seed, acceptance_seed=49001+seed)
        result['arms']['portfolio'] = portfolio(evaluator, candidate, problem.units, seed=39001+seed, acceptance_seed=49001+seed)
        result['status'] = 'completed'
        result['evaluations'] = sum(w['evaluations'] for w in result['policies']) + sum(a['evaluations'] for a in result['arms'].values())
    result['elapsed_seconds'] = monotonic()-started
    write_json(output/'trials'/f"{row['case_id']}-{seed}.json", result)
    print('COMPLETE', row['case_id'], seed, result['status'], flush=True)
    return result


def qualify(rows, public, retained):
    """Fixed per-seed and all-seed gates; failures stay in their denominators."""
    per_seed = {}
    for seed in SEEDS:
        group = [r for r in rows if r['search_seed'] == seed]
        counts = {kind: sum(r[kind+'_pass'] for r in group) for kind in ('recovery', 'transfer')}
        cells = {kind: len({(public[r['case_id']]['language'], public[r['case_id']]['spacing'])
                           for r in group if r[kind+'_pass']}) for kind in ('recovery', 'transfer')}
        per_seed[str(seed)] = dict(counts=counts, cells=cells,
                                  pass_gate=all(counts[k] >= 6 and cells[k] == 4 for k in counts))
    consistent = [case for case in public if all(r['recovery_pass'] and r['transfer_pass']
                  for r in rows if r['case_id'] == case) and sum(r['case_id'] == case for r in rows) == 3]
    return dict(per_seed=per_seed, consistent_cases=consistent,
                qualifies=all(v['pass_gate'] for v in per_seed.values()) and len(consistent) >= 6 and retained)


def assess(output, searches):
    public = {r['case_id']: r for r in read_json(output/'public_inputs.json')}
    private = {r['case_id']: r for r in read_json(output/'fixture_truth.json')}
    methods = {m: [] for m in METHODS}
    records = {m: {case: [] for case in public} for m in METHODS}
    for search in searches:
        case = search['case_id']
        row, truth = public[case], private[case]
        for name in METHODS:
            assessment = dict(case_id=case, search_seed=search['search_seed'], status=search['status'],
                              recovery_pass=False, transfer_pass=False)
            if search['status'] == 'completed':
                saved = search['arms'][name]['best']
                prefixes = search['selected']['policy']['prefixes']
                assessment['true_parser_selected'] = prefixes == truth['prefixes']
                assessment['before'] = recovery_metrics(search['selected']['best']['payload']['plaintext'].replace('\n', ''), ''.join(truth['truth_spans']))
                assessment['recovery'] = recovery_metrics(saved['payload']['plaintext'].replace('\n', ''), ''.join(truth['truth_spans']))
                transfer = frozen_decode(truth['transfer_spans'], prefixes, row['spacing'], saved['payload']['table'], model(training_text(row), 4))
                prediction = ''.join(s['plaintext'] if s['valid'] else '?'*len(t) for s, t in zip(transfer['spans'], truth['transfer_truth']))
                assessment['transfer'] = recovery_metrics(prediction, ''.join(truth['transfer_truth']))
                assessment['transfer_decoding'] = transfer
                assessment['recovery_pass'] = assessment['recovery']['nonspace_edit_accuracy'] >= .9
                assessment['transfer_pass'] = assessment['transfer']['nonspace_edit_accuracy'] >= .9
                records[name][case].append(dict(prefixes=prefixes, plaintext=saved['payload']['plaintext']))
            else:
                records[name][case].append(None)
            methods[name].append(assessment)
    retained = all(private[r['case_id']]['prefixes'] in [p['prefixes'] for p in r['structural_policies']] for r in searches)
    summaries = {}
    for method, rows in methods.items():
        flags = {case: stability(r) for case, r in records[method].items()}
        for case, flag in flags.items():
            flag['all_seeds_correct'] = all(r['recovery_pass'] for r in rows if r['case_id'] == case)
            flag['false_confidence'] = flag['flag'] and not flag['all_seeds_correct']
        summaries[method] = dict(**qualify(rows, public, retained), stability=flags)
    write_json(output/'evidence.json', dict(methods=methods, summaries=summaries,
               true_parsers_retained=retained, evaluations=sum(r['evaluations'] for r in searches),
               label='Prospective clean synthetic comparison; not manuscript evidence'))
    print('QUALIFICATION', {m: s['qualifies'] for m, s in summaries.items()}, flush=True)


def run(output, workers):
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'manifest.json', dict(environment=environment(ROOT), protocol_hash=file_hash(PROTOCOL),
               source_hashes={k: file_hash(v) for k, v in SOURCES.items()}, seeds=SEEDS, methods=METHODS,
               optimization_cap=6881280, workers=workers))
    public = prepare(output)
    tasks = [(row, seed, str(output)) for row in public for seed in SEEDS]
    if workers == 1:
        searches = [solve(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            searches = list(pool.map(solve, tasks))
    assess(output, searches)


def verify(output):
    checked = 0
    for row in read_json(output/'public_inputs.json'):
        for seed in SEEDS:
            trial = read_json(output/'trials'/f"{row['case_id']}-{seed}.json")
            items = [(p['policy']['prefixes'], p['best']) for p in trial['policies']]
            if trial['status'] == 'completed':
                prefixes = trial['selected']['policy']['prefixes']
                items += [(prefixes, a['best']) for a in trial['arms'].values()]
                items += [(prefixes, a['best']) for a in trial['arms']['portfolio']['arms'].values()]
            for prefixes, saved in items:
                evaluator = GroupedEvaluator(GroupedProblem(tuple(row['spans']), training_text(row), tuple(prefixes), row['spacing']))
                value = evaluator(Candidate.create(**saved['candidate']))
                if value.payload != saved['payload'] or dict(value.score.components) != saved['components'] or sum(v for _, v in value.score.components) != saved['total_bits']:
                    raise AssertionError('stored candidate replay failed')
                checked += 1
    write_json(output/'verification.json', dict(exact_replays=checked, evidence_hash=file_hash(output/'evidence.json')))
    print('VERIFIED', checked)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/recovery_reliability_2026-10-11')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        verify(args.output)
    else:
        run(args.output, args.workers)


if __name__ == '__main__':
    main()
