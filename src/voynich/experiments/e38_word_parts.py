"""Preregistered prefix-plus-suffix shape test (stage 38).

Protocol: docs/protocols/WORD_PARTS_2026-10-10.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import numpy as np

from voynich import mechanism_models as mm
from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e28_word_homophones import save
from voynich.experiments.e37_ending_markers import IT, SPLIT, ZL, select
from voynich.laboratory.manifest import environment
from voynich.laboratory.word_parts import ProductModel, contrast, folds
from voynich.laboratory.word_shapes import NGramModel
from voynich.paths import ROOT

PROTOCOL = ROOT/'docs/protocols/WORD_PARTS_2026-10-10.md'
NAIBBE = ROOT/'data/naibbe_cipher_pre.txt'
LATIN = ROOT/'data/latin_alfonsi.txt'
ITALIAN = ROOT/'data/italian_dante.txt'
K = 5


def tokens(lines):
    """(folio, word) for every clean paragraph token, in manuscript order."""
    return [(ln['folio'], w['word']) for ln in lines for w in ln['words'] if w['clean']]


def folio_folds(pairs):
    assignment = folds([folio for folio, _ in pairs], K)
    return [([w for f, w in pairs if assignment[f] != k], [w for f, w in pairs if assignment[f] == k]) for k in range(K)]


def block_folds(words):
    size = len(words)//K
    return [(words[:k*size] + words[(k+1)*size:], words[k*size:(k+1)*size]) for k in range(K)]


def brief(result):
    inv = result['inventory']
    return dict({k: v for k, v in result.items() if k != 'inventory'},
                effective_prefixes=float(inv['effective_prefixes']), effective_suffixes=float(inv['effective_suffixes']),
                prefixes=inv['prefixes'], suffixes=inv['suffixes'])


def evaluate(pairs_of_folds):
    out = [brief(contrast(train, held)[0]) for train, held in pairs_of_folds]
    values = [r['T_new'] for r in out]
    return dict(folds=out, T_new=values, mean_T_new=float(np.mean(values)), mean_T=float(np.mean([r['T'] for r in out])),
                mean_coverage_new=float(np.mean([r['coverage_new'] for r in out])),
                positive=sum(v > 0 for v in values), negative=sum(v < 0 for v in values))


def chain_folds(pairs_of_folds, seed):
    """For each fold: chain text sampled from a glyph chain trained on that fold's training words."""
    out = []
    for k, (train, held) in enumerate(pairs_of_folds):
        model, rng = NGramModel(train, 2), np.random.default_rng(seed + k)
        out.append(([model.sample(rng) for _ in range(len(train))], [model.sample(rng) for _ in range(len(held))]))
    return out


def plain_words(path, limit=35000):
    return re.findall('[a-z]+', path.read_text().lower())[:limit]


def inventory(words):
    inv = ProductModel(words).inventory()
    return dict(prefixes=inv['prefixes'], suffixes=inv['suffixes'],
                effective_prefixes=float(inv['effective_prefixes']), effective_suffixes=float(inv['effective_suffixes']),
                top_prefixes=[[p, float(v)] for p, v in inv['top_prefixes']],
                top_suffixes=[[s, float(v)] for s, v in inv['top_suffixes']])


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT/'src/voynich/laboratory/word_parts.py', ROOT/'src/voynich/laboratory/word_shapes.py',
             ROOT/'src/voynich/experiments/e37_ending_markers.py', ROOT/'src/voynich/mechanism_models.py',
             ZL, IT, SPLIT, NAIBBE, LATIN, ITALIAN, PROTOCOL]
    save(output/'manifest.json', dict(environment=environment(ROOT),
                                      hashes={str(p.relative_to(ROOT)): sha(p) for p in paths}))
    lines = select(ZL, 'B')
    b = tokens(lines)
    b_folds = folio_folds(b)
    naibbe = [w for w in NAIBBE.read_text().split() if re.fullmatch('[a-z]+', w)]
    naibbe_folds = block_folds(naibbe)
    calibration = dict(naibbe=evaluate(naibbe_folds),
                       chain_from_naibbe=evaluate(chain_folds(naibbe_folds, 3801)),
                       chain_from_voynich=evaluate(chain_folds(b_folds, 3811)))
    gate = (calibration['naibbe']['positive'] >= 4 and calibration['chain_from_naibbe']['negative'] >= 4
            and calibration['chain_from_voynich']['negative'] >= 4)
    calibration['gate_passed'] = gate
    save(output/'calibration.json', calibration)
    print('calibration', gate, {k: [round(x, 2) for x in v['T_new']] for k, v in calibration.items() if isinstance(v, dict)}, flush=True)
    evidence = dict(status='structural test of prefix-plus-suffix word shape; no key search, no readings',
                    calibration_gate_passed=gate)
    if gate:
        voynich = evaluate(b_folds)
        controls = [v for name in ('chain_from_naibbe', 'chain_from_voynich') for v in calibration[name]['T_new']]
        if voynich['positive'] >= 4 and voynich['mean_coverage_new'] >= .95 and voynich['mean_T_new'] > max(controls):
            verdict = 'product-like'
        elif voynich['negative'] >= 4:
            verdict = 'chain-like'
        else:
            verdict = 'mixed'
        evidence.update(manuscript_B=voynich, verdict=verdict, manuscript_B_inventory=inventory([w for _, w in b]),
                        naibbe_inventory=inventory(naibbe),
                        IT2a_B=evaluate(folio_folds(tokens(select(IT, 'B')))),
                        ZL_A_non_sealed=evaluate(folio_folds(tokens(select(ZL, 'A')))))
        generated, _ = mm.generate(mm.Training(lines), None, '', len(b), dict(mechanism='copy', level=2, coupling=1), 101)
        evidence['R2'] = evaluate(folio_folds([(f, w) for (f, _), w in zip(b, generated)]))
        evidence['latin'] = evaluate(block_folds(plain_words(LATIN)))
        evidence['italian'] = evaluate(block_folds(plain_words(ITALIAN)))
    save(output/'evidence.json', evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/word_parts_2026-10-10')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
