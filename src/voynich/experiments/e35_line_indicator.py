"""Preregistered test for a line-initial indicator (stage 35).

Does the first glyph of a line predict later word endings in that line more
than other words in the line do? Protocol: docs/protocols/LINE_INDICATOR_2026-10-10.md.
"""
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
from voynich.laboratory.manifest import environment
from voynich.paths import ROOT
from voynich.voynich_core import eva_glyphs

ZL = ROOT/'data/ZL3b-n.txt'
SPLIT = ROOT/'results/image_annotation_pilot_2026-10-10/split.json'
PROTOCOL = ROOT/'docs/protocols/LINE_INDICATOR_2026-10-10.md'
POSITIONS = (1, 2, 3, 4)
MIN_WORDS = 9
FEATURES = {'final': lambda w: eva_glyphs(w)[-1], 'initial': lambda w: eva_glyphs(w)[0], 'word': lambda w: w}
Q_VALUES = (0., .05, .1, .2, .4)


def select(lines, keep):
    """Qualifying lines as dicts with page, folio, paragraph flag and word strings."""
    out = []
    for ln in lines:
        if not keep(ln) or len(ln['words']) < MIN_WORDS or not all(w['clean'] for w in ln['words'][:MIN_WORDS]):
            continue
        out.append(dict(page=ln['page'], folio=ln['folio'], pstart=bool(ln['paragraph_start']),
                        words=[w['word'] for w in ln['words'][:MIN_WORDS]]))
    return out


def _codes(values):
    table = {}
    return np.array([table.setdefault(v, len(table)) for v in values]), len(table)


def _mi(k, f, nk, nf):
    joint = np.bincount(k*nf + f, minlength=nk*nf).reshape(nk, nf).astype(float)
    n = joint.sum()
    rows, cols = joint.sum(axis=1, keepdims=True), joint.sum(axis=0, keepdims=True)
    mask = joint > 0
    return float((joint[mask]/n*np.log2(joint[mask]*n/(rows @ cols)[mask])).sum())


def _entropy(k, nk):
    p = np.bincount(k, minlength=nk)/len(k)
    p = p[p > 0]
    return float(-(p*np.log2(p)).sum())


def position_contributions(lines, j, feature, *, permutations=199, seed=3501):
    """Per-page sums for key position j: tokens, excess-bit mass and key-entropy mass."""
    keys, nk = _codes([eva_glyphs(ln['words'][j-1])[0] for ln in lines])
    feats, nf = _codes([FEATURES[feature](w) for ln in lines for w in ln['words'][j+1:j+5]])
    feats = feats.reshape(len(lines), 4)
    strata = defaultdict(list)
    for i, ln in enumerate(lines):
        strata[(ln['page'], ln['pstart'])].append(i)
    rng = np.random.default_rng(seed + j)
    pages = defaultdict(lambda: np.zeros(3))
    for (page, _), ix in strata.items():
        ix = np.array(ix)
        k, f = keys[ix], feats[ix].ravel()
        raw = _mi(np.repeat(k, 4), f, nk, nf)
        null = np.mean([_mi(np.repeat(rng.permutation(k), 4), f, nk, nf) for _ in range(permutations)])
        n = len(f)
        pages[page] += (n, n*(raw-null), n*_entropy(k, nk))
    return dict(pages)


def analyse(lines, feature='final', *, bootstrap=2000, seed=3502):
    per = {j: position_contributions(lines, j, feature) for j in POSITIONS}
    pages = sorted(per[1])
    mass = np.array([[per[j][p] for p in pages] for j in POSITIONS])      # position x page x (n, excess, entropy)

    def summary(index):
        total = mass[:, index].sum(axis=1)
        excess = total[:, 1]/total[:, 0]
        entropy = total[:, 2]/total[:, 0]
        normalised = excess/entropy
        return excess, normalised, excess[0]-excess[1:].mean(), normalised[0]-normalised[1:].mean()

    excess, normalised, d, dn = summary(np.arange(len(pages)))
    rng = np.random.default_rng(seed)
    boots = np.array([summary(rng.integers(len(pages), size=len(pages)))[2] for _ in range(bootstrap)])
    folios = list(dict.fromkeys(ln['folio'] for ln in lines))
    half_of = {f: i % 2 for i, f in enumerate(folios)}
    page_half = {ln['page']: half_of[ln['folio']] for ln in lines}
    halves = [float(summary(np.array([i for i, p in enumerate(pages) if page_half[p] == h]))[2]) for h in (0, 1)]
    interval = np.quantile(boots, [.025, .975]).tolist()
    return dict(feature=feature, lines=len(lines), pages=len(pages), excess=excess.tolist(),
                normalised=normalised.tolist(), D=float(d), D_normalised=float(dn), D_interval=interval,
                D_halves=halves,
                fires=bool(d > 0 and interval[0] > 0 and min(halves) > 0 and dn > 0))


def shuffle_first_words(lines, seed):
    """Permute first words among lines within stratum: destroys any key/line association."""
    rng = np.random.default_rng(seed)
    strata = defaultdict(list)
    for i, ln in enumerate(lines):
        strata[(ln['page'], ln['pstart'])].append(i)
    out = [dict(ln, words=list(ln['words'])) for ln in lines]
    for ix in strata.values():
        for dest, src in zip(ix, rng.permutation(ix)):
            out[dest]['words'][0] = lines[int(src)]['words'][0]
    return out


def plant(lines, q, seed):
    """Lines whose first glyph falls in the upper key half get endings remapped with probability q."""
    counts = Counter(eva_glyphs(ln['words'][0])[0] for ln in lines)
    upper, running = set(), 0
    for glyph in sorted(counts):
        if running >= sum(counts.values())/2:
            upper.add(glyph)
        running += counts[glyph]
    finals = sorted({eva_glyphs(w)[-1] for ln in lines for w in ln['words']})
    remap = dict(zip(finals, finals[1:] + finals[:1]))
    rng = np.random.default_rng(seed)
    out = []
    for ln in lines:
        words = list(ln['words'])
        if eva_glyphs(words[0])[0] in upper:
            for i in range(1, len(words)):
                if rng.random() < q:
                    glyphs = eva_glyphs(words[i])
                    words[i] = ''.join(glyphs[:-1] + [remap[glyphs[-1]]])
        out.append(dict(ln, words=words))
    return out


def r2_lines(lines, training_lines, config, seed):
    tokens, _ = mm.generate(mm.Training(training_lines), None, '', MIN_WORDS*len(lines), config, seed)
    return [dict(ln, words=tokens[i*MIN_WORDS:(i+1)*MIN_WORDS]) for i, ln in enumerate(lines)]


def load():
    raw = load_lines(ZL)
    split = json.loads(SPLIT.read_text())['sets']
    sealed = set(split['confirmation_X']['pages']) | set(split['confirmation_Y']['pages'])
    development = set(split['development']['pages'])
    b_raw = [ln for ln in raw if ln['meta'].get('L') == 'B' and ln['page'] not in sealed]
    return (select(raw, lambda ln: ln['meta'].get('L') == 'B' and ln['page'] not in sealed),
            select(raw, lambda ln: ln['page'] in development), b_raw)


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT/'src/voynich/mechanism_models.py', ZL, SPLIT, PROTOCOL]
    save(output/'manifest.json', dict(environment=environment(ROOT),
                                      hashes={str(p.relative_to(ROOT)): sha(p) for p in paths}))
    b, a_dev, b_raw = load()
    null = shuffle_first_words(b, 3503)
    calibration = {}
    for q in Q_VALUES:
        runs = [analyse(plant(shuffle_first_words(b, 3600+r), q, 3504+r)) for r in range(20)]
        calibration[str(q)] = dict(fired=sum(r['fires'] for r in runs), total=20,
                                   D=[r['D'] for r in runs])
        print('planted', q, calibration[str(q)]['fired'], flush=True)
    gate = calibration['0.0']['fired'] <= 2 and calibration['0.4']['fired'] >= 16
    detectable = next((q for q in Q_VALUES[1:] if calibration[str(q)]['fired'] >= 16), None)
    save(output/'calibration.json', dict(q=calibration, gate_passed=gate, smallest_detected_q=detectable))
    evidence = dict(status='structural test of a line-initial first-glyph indicator; no readings',
                    calibration_gate_passed=gate, smallest_detected_q=detectable,
                    shuffled_keys=analyse(null))
    if gate:
        evidence['manuscript_B'] = {f: analyse(b, f) for f in FEATURES}
        evidence['manuscript_A_development'] = analyse(a_dev)
        evidence['R2'] = {f'level2_coupling{c}': [analyse(r2_lines(b, b_raw, dict(mechanism='copy', level=2, coupling=c), s))
                                                  for s in range(101, 107)] for c in (0, 1)}
    save(output/'evidence.json', evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/line_indicator_2026-10-10')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
