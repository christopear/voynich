"""Shared stage-31-style forward screen for codebook variants (stages 32 onward).

The selection, calibration, discrimination and reserved comparison follow the
stage-31 protocol exactly. Callers supply how codebooks are built and how a
plaintext passage is encrypted onto manuscript rows.
"""
from __future__ import annotations

from collections import Counter
import json

import numpy as np
from scipy.stats import spearmanr

from voynich import mechanism_models as mm
from voynich.experiments.e28_word_homophones import save
from voynich.experiments.e30_structured_word_codes import R2
from voynich.experiments.e31_word_shapes import (
    NAMES, PREPARED, SCALES, STAGE28, closest, discrimination, distance, medians, profile,
)
from voynich.laboratory.word_shapes import NGramModel, stratified_decomposition
from voynich.voynich_core import eva_glyphs


def vocabulary():
    return sorted({w for ch in json.loads(PREPARED.read_text())['cucina'] for w in ch['words']})


def source_frequencies():
    return Counter(w for ch in json.loads(PREPARED.read_text())['cucina'] for w in ch['words'])


def passages():
    return [dict(p, words=p['words'][:512], spans=p['spans'][:8]) for p in json.loads(STAGE28.read_text())['cucina']]


def frequency_length(tokens):
    counts = Counter(tokens)
    types = sorted(counts)
    if len(types) < 3:
        return None
    return float(spearmanr([counts[w] for w in types], [len(eva_glyphs(w)) for w in types]).statistic)


def broad_model(arms):
    return NGramModel([w for ws in arms['broad'].values() for w in ws], 2)


def generate(books, rules, encrypt, panels, train, dev, val):
    records = []
    for panel in panels:
        rows = dev if panel['split'] == 'development' else val
        for seed, book in books.items():
            for setting, rule in enumerate(rules):
                tokens, audit = encrypt(book, panel['words'], rows, rule, 10000+100*panel['seed']+seed)
                assert book.decrypt(tokens) == panel['words']
                records.append(dict(family='cipher', split=panel['split'], setting=setting, rule=rule, seed=seed,
                                    passage=panel['seed'], tokens=tokens, audit=audit, profile=profile(tokens, rows),
                                    frequency_length=frequency_length(tokens)))
    for split, rows, seeds in [('development', dev, range(101, 107)), ('validation', val, range(201, 207))]:
        for setting, config in enumerate(R2):
            for seed in seeds:
                tokens, audit = mm.generate(train, None, '', 512, config, seed)
                records.append(dict(family='R2', split=split, setting=setting, config=config, seed=seed,
                                    tokens=tokens, audit=audit, profile=profile(tokens, rows),
                                    frequency_length=frequency_length(tokens)))
    return records


def calibrate(make_book, rules, encrypt, panels, dev, development):
    candidates = medians(development, 'cipher')
    out = []
    for key_seed in (701, 702):
        book = make_book(key_seed)
        for panel in [p for p in panels if p['split'] == 'development']:
            for rule in rules:
                tokens, _ = encrypt(book, panel['words'], dev, rule, 10000+100*panel['seed']+key_seed)
                assert book.decrypt(tokens) == panel['words']
                measured = profile(tokens, dev)
                out.append(dict(key_seed=key_seed, passage=panel['seed'], rule=rule, profile=measured,
                                selected=closest(measured['vector'], candidates)))
    passed = sum(c['selected']['distance'] <= 2 for c in out)
    return dict(passed=passed, total=len(out), gate=12, records=out, discrimination=discrimination(development))


def compare(records, targets, hands):
    def hand_excess(tokens, rows):
        return stratified_decomposition(tokens, rows, [(r['section'], hands[r['page']]) for r in rows])['total']['excess']

    measured = {name: dict(profile=profile([r['word'] for r in rows], rows),
                           hand_section_excess=hand_excess([r['word'] for r in rows], rows),
                           frequency_length=frequency_length([r['word'] for r in rows]))
                for name, rows in targets.items()}
    development = [r for r in records if r['split'] == 'development']
    target = measured['B_ZL_split_early']['profile']['vector']
    selection = {f: closest(target, medians(development, f)) for f in ('cipher', 'R2')}
    comparisons = {}
    for family, chosen in selection.items():
        comparisons[family] = {}
        for name, observed in measured.items():
            split = 'development' if name.endswith('early') else 'validation'
            rows = targets[name]
            draws = []
            for record in records:
                if (record['family'], record['setting'], record['split']) != (family, chosen['setting'], split):
                    continue
                prof = record['profile'] if name in ('B_ZL_split_early', 'B_ZL_split_late') else profile(record['tokens'], rows)
                draws.append(dict(seed=record['seed'], passage=record.get('passage'), profile=prof,
                                  hand_section_excess=hand_excess(record['tokens'], rows),
                                  distance=distance(prof['vector'], observed['profile']['vector']),
                                  signed_residual=(np.array(prof['vector'])-observed['profile']['vector']).tolist()))
            comparisons[family][name] = dict(hits=sum(d['distance'] <= 1 for d in draws), total=len(draws), draws=draws)
    return dict(names=NAMES, scales=SCALES.tolist(), targets=measured, selection=selection, comparisons=comparisons)


def run_screen(output, *, books, make_book, rules, encrypt, r2_lines, targets, hands):
    """Generate, calibrate, then (if calibrated) select and compare. Saves generated/calibration."""
    panels = passages()
    save(output/'source_panels.json', panels)
    dev, val = targets['B_ZL_split_early'], targets['B_ZL_split_late']
    train = mm.Training(r2_lines)
    records = generate(books, rules, encrypt, panels, train, dev, val)
    save(output/'generated.json', records)
    development = [r for r in records if r['split'] == 'development']
    calibration = calibrate(make_book, rules, encrypt, panels, dev, development)
    save(output/'calibration.json', calibration)
    if calibration['passed'] < 12:
        return dict(status='calibration failed; manuscript profile comparison stopped',
                    calibration_passed=calibration['passed'])
    return dict(status='descriptive forward-model screen; no key recovery or readings',
                calibration_passed=calibration['passed'],
                balanced_accuracy=calibration['discrimination']['balanced_accuracy'],
                **compare(records, targets, hands))
