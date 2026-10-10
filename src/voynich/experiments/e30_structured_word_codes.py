"""Preregistered structured word-code/persistence screen against copy-and-modify."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

import numpy as np

from voynich import mechanism_models as mm
from voynich.experiments.e06_boundary_frontier import load_lines
from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e28_word_homophones import save
from voynich.experiments.e29_frequency_currier_a import decomposition
from voynich.laboratory.manifest import environment
from voynich.laboratory.structured_codes import (
    RULES, SlotGrammar, WordCodebook, glyph_profile, order_diagnostic, serialized_bits,
)
from voynich.paths import ROOT

NAMES = ['ttr', 'top10', 'section_excess', 'role_excess', 'frequent_excess', 'mean_length', 'glyph_h']
SCALES = np.array([.05, .04, .05, .05, .05, .5, .25])
R2 = [dict(mechanism='copy', level=level, coupling=c) for level in range(3) for c in (0, 1)]


def profile(tokens, rows):
    section = decomposition(tokens, rows)
    roles = decomposition(tokens, rows, 'roles')
    counts = Counter(tokens)
    glyph = glyph_profile(tokens)
    vector = [len(counts)/len(tokens), sum(v for _, v in counts.most_common(10))/len(tokens),
              section['total']['excess'], roles['total']['excess'],
              section['bins']['count5plus']['excess'], glyph['mean_length'], glyph['conditional_entropy']]
    return dict(vector=vector, section=section, roles=roles, glyph=glyph)


def distance(a, b):
    return float(np.max(np.abs(np.array(a)-np.array(b))/SCALES))


def medians(records, family):
    out = {}
    for setting in sorted({r['setting'] for r in records if r['family'] == family}):
        values = [r['profile']['vector'] for r in records if r['family'] == family and r['setting'] == setting]
        out[setting] = np.median(values, axis=0).tolist()
    return out


def closest(vector, candidates):
    return min((dict(setting=setting, distance=distance(vector, median), median=median)
                for setting, median in candidates.items()), key=lambda r: (r['distance'], r['setting']))


def training_lines(rows):
    originals = {ln['locus']: ln for ln in load_lines(ROOT/'data/ZL3b-n.txt')}
    groups = defaultdict(list)
    for row in rows:
        groups[row['locus']].append(row)
    out = []
    for locus, group in groups.items():
        line = originals[locus]
        gaps = [line['gaps'][a['end']] if a['end']+1 == b['start'] else 'hard'
                for a, b in zip(group, group[1:])]
        out.append(dict(line, words=[dict(word=r['word'], clean=True) for r in group], gaps=gaps))
    return out


def model_description(value):
    if isinstance(value, mm.Weighted):
        return dict(values=value.values, cumulative_weights=value.cum)
    if isinstance(value, dict):
        return {repr(k): model_description(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [model_description(v) for v in value]
    return value


def discrimination(records):
    predictions = []
    for record in records:
        # R2 validation seeds differ; only the six development seed IDs enter here.
        remaining = [r for r in records if r['seed'] != record['seed']]
        scores = {family: closest(record['profile']['vector'], medians(remaining, family))['distance']
                  for family in ('cipher', 'R2')}
        prediction = min(scores, key=lambda family: (scores[family], family))
        predictions.append(dict(family=record['family'], setting=record['setting'], seed=record['seed'],
                                passage=record.get('passage'), prediction=prediction, distances=scores))
    accuracies = {family: sum(p['prediction'] == family for p in predictions if p['family'] == family)/
                  sum(p['family'] == family for p in predictions) for family in ('cipher', 'R2')}
    return dict(by_family=accuracies, balanced_accuracy=sum(accuracies.values())/2,
                passed=sum(accuracies.values())/2 >= .8, predictions=predictions)


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    stage29 = ROOT/'results/frequency_currier_a_2026-10-09/slots.json'
    stage28 = ROOT/'results/word_homophones_2026-10-09/source_panels.json'
    prepared = ROOT/'results/unit_association_2026-10-09/prepared_sources.json'
    slots = json.loads(stage29.read_text())
    targets = {name: slots[name] for name in ('B_ZL_split_early', 'B_ZL_split_late',
               'B_IT_split_late', 'B_ZL_join_late', 'A_ZL_split_late')}
    dev = targets['B_ZL_split_early']
    val = targets['B_ZL_split_late']
    save(output/'slots.json', targets)
    panels = [dict(p, words=p['words'][:512], spans=p['spans'][:8])
              for p in json.loads(stage28.read_text())['cucina']]
    save(output/'source_panels.json', panels)
    vocabulary = sorted({w for chapter in json.loads(prepared.read_text())['cucina'] for w in chapter['words']})
    grammar = SlotGrammar.fit([r['word'] for r in dev])
    description = grammar.description()
    description['coverage'] = {name: grammar.coverage([r['word'] for r in rows], [r['word'] for r in dev])
                               for name, rows in targets.items()}
    description['required_codewords'] = 2*len(vocabulary)
    save(output/'grammar.json', description)
    paths = [Path(__file__), ROOT/'src/voynich/laboratory/structured_codes.py',
             ROOT/'src/voynich/mechanism_models.py', stage29, stage28, prepared,
             ROOT/'docs/protocols/STRUCTURED_WORD_CODES_2026-10-09.md']
    save(output/'manifest.json', dict(environment=environment(ROOT),
        hashes={str(p.relative_to(ROOT)): sha(p) for p in paths}))
    if len(grammar.weights) < 2*len(vocabulary):
        save(output/'evidence.json', dict(status='capacity failure for this grammar', grammar=description))
        return
    books = {seed: WordCodebook.make(vocabulary, grammar, seed) for seed in range(101, 107)}
    save(output/'codebooks.json', {seed: book.encode for seed, book in books.items()})
    train = mm.Training(training_lines(dev))
    r2_description = model_description(vars(train))
    save(output/'r2_model.json', r2_description)
    save(output/'costs.json', dict(cipher={seed: book.costs() for seed, book in books.items()},
        grammar_bits=description['serialization_bits'], R2_serialization_bits=serialized_bits(r2_description),
        note='Explicit serialization/reference budgets, not comparable total likelihoods or an MDL ranking.'))
    records = []
    for panel in panels:
        rows = dev if panel['split'] == 'development' else val
        for seed, book in books.items():
            for setting, rule in enumerate(RULES):
                tokens, audit = book.encrypt(panel['words'], [r['page'] for r in rows], rule,
                                            10000+100*panel['seed']+seed)
                assert book.decrypt(tokens) == panel['words']
                records.append(dict(family='cipher', split=panel['split'], setting=setting, rule=rule,
                    seed=seed, passage=panel['seed'], tokens=tokens, audit=audit,
                    profile=profile(tokens, rows), order=order_diagnostic(tokens, rows)))
        print('cipher', panel['split'], panel['seed'], 'complete', flush=True)
    for split, rows, seeds in [('development', dev, range(101, 107)), ('validation', val, range(201, 207))]:
        for setting, config in enumerate(R2):
            for seed in seeds:
                tokens, audit = mm.generate(train, None, '', 512, config, seed)
                records.append(dict(family='R2', split=split, setting=setting, config=config, seed=seed,
                    tokens=tokens, audit=audit, profile=profile(tokens, rows), order=order_diagnostic(tokens, rows)))
        print('R2', split, 'complete', flush=True)
    save(output/'generated.json', records)
    development = [r for r in records if r['split'] == 'development']
    candidates = medians(development, 'cipher')
    calibration = []
    for key_seed in (701, 702):
        book = WordCodebook.make(vocabulary, grammar, key_seed)
        for panel in [p for p in panels if p['split'] == 'development']:
            for rule in RULES:
                tokens, _ = book.encrypt(panel['words'], [r['page'] for r in dev], rule,
                                        10000+100*panel['seed']+key_seed)
                assert book.decrypt(tokens) == panel['words']
                measured = profile(tokens, dev)
                calibration.append(dict(key_seed=key_seed, passage=panel['seed'], rule=rule,
                    profile=measured, selected=closest(measured['vector'], candidates)))
    passed = sum(c['selected']['distance'] <= 2 for c in calibration)
    calibrated = dict(passed=passed, total=16, gate=12, records=calibration,
                      discrimination=discrimination(development))
    save(output/'calibration.json', calibrated)
    if passed < 12:
        save(output/'evidence.json', dict(status='calibration failed; manuscript profile comparison stopped',
                                         calibration_passed=passed))
        return
    measured_targets = {name: dict(profile=profile([r['word'] for r in rows], rows),
                                  order=order_diagnostic([r['word'] for r in rows], rows))
                        for name, rows in targets.items()}
    target = measured_targets['B_ZL_split_early']['profile']['vector']
    selection = {family: closest(target, medians(development, family)) for family in ('cipher', 'R2')}
    comparisons = {}
    for family, chosen in selection.items():
        comparisons[family] = {}
        for name, observed in measured_targets.items():
            split = 'development' if name.endswith('early') else 'validation'
            values = []
            for record in records:
                if (record['family'], record['setting'], record['split']) != (family, chosen['setting'], split):
                    continue
                # Apply identical generated sequences to secondary layouts, recomputing role-sensitive metrics.
                measured = record['profile'] if name in ('B_ZL_split_early', 'B_ZL_split_late') else profile(record['tokens'], targets[name])
                values.append(dict(seed=record['seed'], passage=record.get('passage'), profile=measured,
                    distance=distance(measured['vector'], observed['profile']['vector']),
                    signed_residual=(np.array(measured['vector'])-observed['profile']['vector']).tolist()))
            comparisons[family][name] = dict(hits=sum(v['distance'] <= 1 for v in values), total=len(values), draws=values)
    save(output/'evidence.json', dict(status='descriptive forward-model screen; no key recovery or readings',
        names=NAMES, scales=SCALES.tolist(), targets=measured_targets, selection=selection, comparisons=comparisons))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/structured_word_codes_2026-10-09')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
