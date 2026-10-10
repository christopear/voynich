"""Post hoc corrective rerun of stages 31-34: drawing gaps, per-layout encoding, scribe wording, enumeration.

Protocol: docs/protocols/BOUNDARY_CORRECTION_2026-10-10.md. Historical stage
outputs and their producers are unchanged; this writes a new directory.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np

from voynich import mechanism_models as mm
from voynich.experiments.e06_boundary_frontier import load_lines
from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e28_word_homophones import save
from voynich.experiments import e31_word_shapes as e31
from voynich.experiments.e30_structured_word_codes import R2
from voynich.experiments.e32_ranked_assignment import setup
from voynich.experiments.e34_source_sensitivity import source_data
from voynich.laboratory.boundary_correction import (
    CONTEXT_RULES, annotate, canonical_top, make_context_encrypt, page_encrypt, profile,
)
from voynich.laboratory.codebook_assignment import ranked_codebook
from voynich.laboratory.forward_screen import frequency_length
from voynich.laboratory.manifest import environment
from voynich.laboratory.structured_codes import RULES
from voynich.laboratory.word_shapes import NGramModel, model_codebook, page_hands, stratified_decomposition
from voynich.paths import ROOT

IT = ROOT/'data/mechanisms/IT2a-n.txt'
PROTOCOL = ROOT/'docs/protocols/BOUNDARY_CORRECTION_2026-10-10.md'
VALIDATION = ('B_ZL_split_late', 'B_IT_split_late', 'B_ZL_join_late', 'A_ZL_split_late')
GRIDS = (('random_cucina', 'cucina', 'random', 'page'), ('ranked_cucina', 'cucina', 'ranked', 'page'),
         ('context_cucina', 'cucina', 'ranked', 'context'), ('context_celsus', 'celsus', 'ranked', 'context'),
         ('context_pliny', 'pliny', 'ranked', 'context'))
STORED = {'random_cucina': ROOT/'results/word_shapes_2026-10-09/codebooks.json',
          'ranked_cucina': ROOT/'results/ranked_assignment_2026-10-09/codebooks.json',
          'context_cucina': ROOT/'results/context_choice_2026-10-09/codebooks.json',
          'context_celsus': ROOT/'results/source_sensitivity_2026-10-09/codebooks_celsus.json',
          'context_pliny': ROOT/'results/source_sensitivity_2026-10-09/codebooks_pliny.json'}


def annotated_targets():
    slots = json.loads(e31.STAGE29.read_text())
    by = {'ZL': {ln['locus']: ln for ln in load_lines(e31.ZL)}, 'IT': {ln['locus']: ln for ln in load_lines(IT)}}
    return {name: annotate(slots[name], by['IT' if '_IT_' in name else 'ZL']) for name in e31.TARGETS}


def grid_books(source, assignment, model):
    vocabulary, frequencies, panels = source_data(source)
    if assignment == 'random':
        make = lambda seed: model_codebook(vocabulary, model, seed)[0]
    else:
        make = lambda seed: ranked_codebook(vocabulary, frequencies, model, seed)[0]
    return {seed: make(seed) for seed in range(101, 107)}, make, panels


def layouts(split):
    return ('B_ZL_split_early',) if split == 'development' else VALIDATION


def generate(books, rules, encrypt, panels, r2_streams, targets):
    records = []
    for panel in panels:
        for seed, book in books.items():
            for setting, rule in enumerate(rules):
                for layout in layouts(panel['split']):
                    rows = targets[layout]
                    tokens, audit = encrypt(book, panel['words'], rows, rule, 10000+100*panel['seed']+seed)
                    assert book.decrypt(tokens) == panel['words']
                    records.append(dict(family='cipher', split=panel['split'], layout=layout, setting=setting,
                                        rule=rule, seed=seed, passage=panel['seed'], tokens=tokens, audit=audit,
                                        profile=profile(tokens, rows), frequency_length=frequency_length(tokens)))
    for (split, setting, seed), stream in r2_streams.items():
        for layout in layouts(split):
            rows = targets[layout]
            records.append(dict(family='R2', split=split, layout=layout, setting=setting, config=R2[setting],
                                seed=seed, profile=profile(stream['tokens'], rows),
                                frequency_length=frequency_length(stream['tokens'])))
    return records


def calibrate(make, rules, encrypt, panels, dev_rows, development):
    candidates = e31.medians(development, 'cipher')
    out = []
    for key_seed in (701, 702):
        book = make(key_seed)
        for panel in [p for p in panels if p['split'] == 'development']:
            for rule in rules:
                tokens, _ = encrypt(book, panel['words'], dev_rows, rule, 10000+100*panel['seed']+key_seed)
                assert book.decrypt(tokens) == panel['words']
                measured = profile(tokens, dev_rows)
                out.append(dict(key_seed=key_seed, passage=panel['seed'], rule=rule, vector=measured['vector'],
                                selected=e31.closest(measured['vector'], candidates)))
    return dict(passed=sum(c['selected']['distance'] <= 2 for c in out), total=len(out), gate=12, records=out)


def compare(records, targets, hands):
    def hand_excess(tokens, rows):
        return stratified_decomposition(tokens, rows, [(r['section'], hands[r['page']]) for r in rows])['total']['excess']

    measured = {name: dict(vector=profile([r['word'] for r in rows], rows)['vector'],
                           hand_section_excess=hand_excess([r['word'] for r in rows], rows),
                           frequency_length=frequency_length([r['word'] for r in rows]))
                for name, rows in targets.items()}
    development = [r for r in records if r['split'] == 'development']
    target = measured['B_ZL_split_early']['vector']
    selection = {f: e31.closest(target, e31.medians(development, f)) for f in ('cipher', 'R2')}
    comparisons, all_rules = {}, {}
    for name, observed in measured.items():
        for r in records:
            if r['layout'] == name:
                r.setdefault('distance', {})[name] = e31.distance(r['profile']['vector'], observed['vector'])
    for family, chosen in selection.items():
        comparisons[family] = {}
        for name, observed in measured.items():
            draws = [r for r in records if (r['family'], r['setting'], r['layout']) == (family, chosen['setting'], name)]
            comparisons[family][name] = dict(
                hits=sum(r['distance'][name] <= 1 for r in draws), total=len(draws),
                best=min(r['distance'][name] for r in draws),
                median_vector=np.median([r['profile']['vector'] for r in draws], axis=0).tolist(),
                median_signed_scaled=np.median([(np.array(r['profile']['vector'])-observed['vector'])/e31.SCALES
                                                for r in draws], axis=0).tolist())
    for setting in sorted({r['setting'] for r in records if r['family'] == 'cipher'}):
        all_rules[setting] = {name: dict(hits=sum(r['distance'][name] <= 1 for r in records
                                                  if r['family'] == 'cipher' and r['setting'] == setting and r['layout'] == name),
                                         best=min(r['distance'][name] for r in records
                                                  if r['family'] == 'cipher' and r['setting'] == setting and r['layout'] == name))
                              for name in measured}
    return dict(targets=measured, selection=selection, comparisons=comparisons, all_rules=all_rules)


def scribe_direct(hands, sources):
    slots = json.loads(e31.STAGE29.read_text())
    full = slots['B_ZL_split_full']

    def measure(tokens, rows):
        section = [r['section'] for r in rows]
        page = stratified_decomposition(tokens, rows, section)
        within = stratified_decomposition(tokens, rows, [(r['section'], hands[r['page']]) for r in rows])
        hand = stratified_decomposition(tokens, [dict(r, page=hands[r['page']]) for r in rows], section)
        return dict(page_excess=page['total']['excess'], within_hand_excess=within['total']['excess'],
                    reduction_share=1-within['total']['excess']/page['total']['excess'] if page['total']['excess'] else None,
                    direct_hand_excess=hand['total']['excess'],
                    raw=dict(page=page['total']['raw'], within_hand=within['total']['raw'], hand=hand['total']['raw']),
                    raw_chain_rule_residual=page['total']['raw']-within['total']['raw']-hand['total']['raw'])
    return dict(manuscript={name: measure([r['word'] for r in rows], rows) for name, rows in slots.items()},
                reference={f"{s}_{p['split']}_{p['seed']}": measure(p['words'], full)
                           for s, ps in sources.items() for p in ps})


def enumeration_check(arms, targets):
    stage31 = json.loads((ROOT/'results/word_shapes_2026-10-09/shapes.json').read_text())
    out = {}
    for arm, by_folio in arms.items():
        words = [w for ws in by_folio.values() for w in ws]
        seen = set(words)
        for order in (1, 2, 3):
            model = NGramModel(words, order)
            for k in e31.K_VALUES:
                old = [w for w, _ in model.top(k)]
                new = [w for w, _ in canonical_top(model, k)]
                cov = {t: e31.coverage(new, [r['word'] for r in targets[t]], seen) for t in VALIDATION}
                stored = stage31['arms'][arm]['models'][f'N{order}']['coverage']
                out[f'{arm}_N{order}_{k}'] = dict(
                    old_distinct=len(set(old)), old_listed=len(old), canonical_distinct=len(new),
                    identical=old == new, coverage=cov,
                    max_token_coverage_change=max(abs(cov[t]['token']-stored[t][str(k)]['token']) for t in VALIDATION))
    return out


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT/'src/voynich/laboratory/boundary_correction.py',
             ROOT/'src/voynich/laboratory/codebook_assignment.py', ROOT/'src/voynich/laboratory/forward_screen.py',
             ROOT/'src/voynich/laboratory/word_shapes.py', ROOT/'src/voynich/experiments/e31_word_shapes.py',
             ROOT/'src/voynich/experiments/e32_ranked_assignment.py',
             ROOT/'src/voynich/experiments/e34_source_sensitivity.py',
             ROOT/'src/voynich/laboratory/structured_codes.py', ROOT/'src/voynich/mechanism_models.py',
             e31.ZL, IT, e31.STAGE29, e31.STAGE28, e31.PREPARED, PROTOCOL, *STORED.values()]
    save(output/'manifest.json', dict(environment=environment(ROOT),
                                      hashes={str(p.relative_to(ROOT)): sha(p) for p in paths}))
    hands = page_hands(e31.ZL)
    targets = annotated_targets()
    save(output/'slots.json', targets)
    _, lines, model = setup()
    _, _, arms = e31.training_arms(json.loads(e31.STAGE29.read_text()))
    save(output/'scribe.json', scribe_direct(hands, json.loads(e31.STAGE28.read_text())))
    save(output/'enumeration.json', enumeration_check(arms, targets))
    print('scribe and enumeration done', flush=True)
    train = mm.Training(lines)
    context = make_context_encrypt(train.edge)
    r2 = {}
    for split, seeds in (('development', range(101, 107)), ('validation', range(201, 207))):
        for setting, config in enumerate(R2):
            for seed in seeds:
                tokens, audit = mm.generate(train, None, '', 512, config, seed)
                r2[(split, setting, seed)] = dict(tokens=tokens, audit=audit)
    save(output/'r2_streams.json', [dict(split=s, setting=k, seed=n, **v) for (s, k, n), v in r2.items()])
    evidence = {}
    for name, source, assignment, kind in GRIDS:
        books, make, panels = grid_books(source, assignment, model)
        assert {str(s): b.encode for s, b in books.items()} == json.loads(STORED[name].read_text()), name
        rules, encrypt = (RULES, page_encrypt) if kind == 'page' else (CONTEXT_RULES, context)
        records = generate(books, rules, encrypt, panels, r2, targets)
        development = [r for r in records if r['split'] == 'development']
        calibration = calibrate(make, rules, encrypt, panels, targets['B_ZL_split_early'], development)
        discrimination = e31.discrimination(development)
        calibration['discrimination'] = dict(by_family=discrimination['by_family'],
                                             balanced_accuracy=discrimination['balanced_accuracy'])
        result = dict(source=source, assignment=assignment, rules=list(rules), calibration_passed=calibration['passed'],
                      balanced_accuracy=discrimination['balanced_accuracy'])
        if calibration['passed'] >= 12:
            result.update(compare(records, targets, hands))
        save(output/f'generated_{name}.json', records)
        save(output/f'calibration_{name}.json', calibration)
        evidence[name] = result
        print(name, 'done', flush=True)
    save(output/'evidence.json', dict(status='post hoc corrective rerun; descriptive forward-model screens; no readings',
                                      names=e31.NAMES, scales=e31.SCALES.tolist(), grids=evidence))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/boundary_correction_2026-10-10')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
