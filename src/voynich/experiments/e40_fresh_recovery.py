"""Frozen grouped recovery on disjoint synthetic passages and unchanged-key transfer."""
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
from voynich.laboratory.grouped_boundary import fixture, space_boundary_f1
from voynich.laboratory.manifest import environment, file_hash
from voynich.paths import ROOT
from voynich.search.grouped import GroupedProblem, GroupedEvaluator, parse_span, frozen_decode
from voynich.search.grouped_pipeline import recover
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import read_json, write_json

PROTOCOL = ROOT/'docs/protocols/FRESH_RECOVERY_2026-10-10.md'
SOURCES = {'celsus': ROOT/'data/laboratory_sources/celsus_medical.txt',
           'pliny': ROOT/'data/laboratory_sources/pliny_medical.txt',
           'dante': ROOT/'data/italian_dante.txt'}


def intervals_overlap(a, b):
    return max(a[0], b[0]) < min(a[1], b[1])


def prepare(output):
    texts = {name: normalize(path.read_text()) for name, path in SOURCES.items()}
    training = {name: (int(.3*len(text)), int(.3*len(text))+min(12000, int(.2*len(text))))
                for name, text in texts.items() if name in ('celsus', 'dante')}
    public, private = [], []
    for language, target, trainer in (('latin', 'pliny', 'celsus'), ('italian', 'dante', 'dante')):
        text = texts[target]
        starts = [int(f*len(text)) for f in (.75, .80)]
        ranges = [(s, s+350) for s in starts] + [(s+1000, s+1350) for s in starts]
        forbidden = [(int(.7*len(text)), int(.7*len(text))+350)]
        if trainer == target:
            forbidden.append(training[trainer])
        if any(b > len(text) for a, b in ranges) or any(
                intervals_overlap(r, other) for i, r in enumerate(ranges)
                for other in ranges[i+1:]+forbidden):
            raise ValueError('overlapping or truncated passage specification')
        lo, hi = training[trainer]
        train = texts[trainer][lo:hi]
        ref = dict(source=trainer, start=lo, stop=hi, raw_hash=file_hash(SOURCES[trainer]),
                   prepared_hash=digest(train))
        for start, seed in zip(starts, (31, 43)):
            plain = text[start:start+350].strip()
            transfer_plain = text[start+1000:start+1350].strip()
            for spacing in ('preserve', 'encoded'):
                case = f'{language}-{spacing}-{seed}'
                spans, truth, table, prefixes = fixture(plain, spacing, seed)
                method = UnitCipher('groups', homophones=2, lengths='variable', spacing=spacing,
                                    alphabet=string.ascii_uppercase[:16])
                key = CipherKey(method.method_id, tuple(table.items()))
                transfer_truth = tuple(textwrap.wrap(transfer_plain, 50, break_long_words=False,
                                                     break_on_hyphens=False))
                transfer = []
                for i, line in enumerate(transfer_truth):
                    encrypted, _ = method.encrypt_text(line, key, seed=140001+seed+i)
                    if spacing == 'encoded':
                        encrypted = ' '.join(encrypted[j:j+5] for j in range(0, len(encrypted), 5))
                    transfer.append(encrypted)
                decoded = tuple(''.join(' ' if c == ' ' else table[c]
                                       for c in parse_span(s, prefixes, spacing)) for s in transfer)
                if decoded != transfer_truth:
                    raise AssertionError('transfer fixture round trip failed')
                pub = dict(case_id=case, language=language, spacing=spacing, seed=seed,
                           spans=spans, training_ref=ref)
                truth_row = dict(case_id=case, truth_spans=truth, table=table, prefixes=prefixes,
                                 target_source=target, start=start, stop=start+350,
                                 target_raw_hash=file_hash(SOURCES[target]), prepared_hash=digest(plain),
                                 transfer_start=start+1000, transfer_stop=start+1350,
                                 transfer_prepared_hash=digest(transfer_plain),
                                 transfer_spans=transfer, transfer_truth=transfer_truth)
                public.append(pub)
                private.append(truth_row)
    write_json(output/'public_inputs.json', public)
    write_json(output/'fixture_truth.json', private)
    return public


def training_text(row):
    ref = row['training_ref']
    path = SOURCES[ref['source']]
    if file_hash(path) != ref['raw_hash']:
        raise ValueError('source changed')
    text = normalize(path.read_text())[ref['start']:ref['stop']]
    if digest(text) != ref['prepared_hash']:
        raise ValueError('training slice changed')
    return text


def solve(task):
    row, output = task
    output = Path(output)
    started = monotonic()
    def progress(index, count, winner):
        write_json(output/'policies'/row['case_id']/f'{index:03}.json', winner)
        print(row['case_id'], 'parser', index+1, '/', count, flush=True)
    result = recover(row['spans'], training_text(row), row['spacing'], row['seed'], progress=progress)
    result.update(case_id=row['case_id'], elapsed_seconds=monotonic()-started)
    write_json(output/'search'/f"{row['case_id']}.json", result)
    return result


def assess(output, searches):
    public = {r['case_id']: r for r in read_json(output/'public_inputs.json')}
    private = {r['case_id']: r for r in read_json(output/'fixture_truth.json')}
    results = []
    for search in searches:
        case = search['case_id']
        row, truth = public[case], private[case]
        result = dict(case_id=case, status=search['status'], evaluations=search['evaluations'],
                      true_parser_retained=truth['prefixes'] in [p['prefixes'] for p in search['screen']['survivors']],
                      recovery_pass=False, transfer_pass=False)
        if search['status'] == 'completed':
            reference = ''.join(truth['truth_spans'])
            for name, saved in (('before', search['selected']['best']), ('after', search['refined']['best'])):
                prediction = saved['payload']['plaintext'].replace('\n', '')
                result[name] = dict(**recovery_metrics(prediction, reference),
                                    space_boundary_f1=space_boundary_f1(prediction, reference))
            prefixes = search['selected']['policy']['prefixes']
            result['true_parser_selected'] = prefixes == truth['prefixes']
            transferred = frozen_decode(truth['transfer_spans'], prefixes, row['spacing'],
                                        search['refined']['best']['payload']['table'], model(training_text(row), 4))
            # An unparseable span is all unknown characters of its true length,
            # used only for error accounting, never to repair a decoding.
            prediction = ''.join(s['plaintext'] if s['valid'] else '?'*len(t)
                                 for s, t in zip(transferred['spans'], truth['transfer_truth']))
            result['transfer'] = dict(**recovery_metrics(prediction, ''.join(truth['transfer_truth'])),
                                      decoding=transferred)
            result['recovery_pass'] = result['after']['nonspace_edit_accuracy'] >= .9
            result['transfer_pass'] = result['transfer']['nonspace_edit_accuracy'] >= .9
        results.append(result)
    cells = {(public[r['case_id']]['language'], public[r['case_id']]['spacing'])
             for r in results if r['recovery_pass']}
    evidence = dict(cases=results, evaluations=sum(r['evaluations'] for r in results),
                    recovery_gate=sum(r['recovery_pass'] for r in results) >= 6 and len(cells) == 4
                                  and all(r['true_parser_retained'] for r in results),
                    transfer_gate=sum(r['transfer_pass'] for r in results) >= 6,
                    evidence_label='Synthetic calibration on disjoint passages; no manuscript evidence')
    write_json(output/'evidence.json', evidence)
    print('GATES', evidence['recovery_gate'], evidence['transfer_gate'], flush=True)


def run(output, workers=4):
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'manifest.json', dict(environment=environment(ROOT), protocol_hash=file_hash(PROTOCOL),
               source_hashes={k: file_hash(v) for k, v in SOURCES.items()}, workers=workers,
               optimization_cap=2162688, beam_budget=4096, continuation_budget=8192, policy_cap=64))
    public = prepare(output)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        searches = list(pool.map(solve, [(r, str(output)) for r in public]))
    # No truth-based assessment occurs until all searches have finished.
    assess(output, searches)


def verify(output):
    calls = 0
    for row in read_json(output/'public_inputs.json'):
        result = read_json(output/'search'/f"{row['case_id']}.json")
        train = training_text(row)
        records = [(w['policy']['prefixes'], w['best']) for w in result['policies']]
        if result['status'] == 'completed':
            records.append((result['selected']['policy']['prefixes'], result['refined']['best']))
        for prefixes, saved in records:
            value = GroupedEvaluator(GroupedProblem(tuple(row['spans']), train, tuple(prefixes), row['spacing']))(
                Candidate.create(**saved['candidate']))
            if value.payload != saved['payload'] or dict(value.score.components) != saved['components']:
                raise AssertionError('saved key replay mismatch')
            calls += 1
    write_json(output/'verification.json', dict(exact_score_replays=calls,
               evidence_hash=file_hash(output/'evidence.json')))
    print('Replayed', calls, 'keys exactly')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/fresh_recovery_2026-10-10')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        verify(args.output)
    else:
        run(args.output, args.workers)


if __name__ == '__main__':
    main()
