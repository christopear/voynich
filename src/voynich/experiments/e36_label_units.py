"""Preregistered label-based diagnostic of unit size (stage 36).

Protocol: docs/protocols/LABEL_UNITS_2026-10-10.md. No label is given a meaning
and no label/drawing alignment is asserted.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import json
from pathlib import Path
import re

import numpy as np

from voynich.experiments.e06_boundary_frontier import parse_body
from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e28_word_homophones import save
from voynich.laboratory.manifest import environment
from voynich.paths import ROOT
from voynich.voynich_core import eva_glyphs

ZL = ROOT/'data/ZL3b-n.txt'
SPLIT = ROOT/'results/image_annotation_pilot_2026-10-10/split.json'
PROTOCOL = ROOT/'docs/protocols/LABEL_UNITS_2026-10-10.md'
NEIGHBOUR_GAPS = ('ordinary', 'uncertain')
ALPHA = .0125
MIN_GLYPHS = 4
PIECE_COUNT = 5


def load():
    split = json.loads(SPLIT.read_text())['sets']
    sealed = set(split['confirmation_X']['pages']) | set(split['confirmation_Y']['pages'])
    labels, words, pairs = [], defaultdict(set), defaultdict(set)
    counts, tally = Counter(), Counter()
    for raw in ZL.read_text().splitlines():
        m = re.match(r'^<(f[^.>]+)\.(\d+\w*),([^>]*)>\s*(.*)$', raw)
        if not m or m[1] in sealed:
            continue
        page, kind = m[1], m[3][1:]
        tokens, gaps = parse_body(m[4])
        if kind.startswith('L'):
            tally['label_loci'] += 1
            if len(tokens) != 1:
                tally['multi_token'] += 1
            elif not tokens[0]['clean']:
                tally['unclean'] += 1
            else:
                labels.append(dict(page=page, kind=kind, word=tokens[0]['word']))
            continue
        for i, token in enumerate(tokens):
            if token['clean']:
                counts[token['word']] += 1
                words[page].add(token['word'])
                if i < len(gaps) and gaps[i] in NEIGHBOUR_GAPS and tokens[i+1]['clean']:
                    pairs[page].add((token['word'], tokens[i+1]['word']))
    return dict(labels=labels, words=dict(words), pairs=dict(pairs), counts=counts, tally=dict(tally))


@lru_cache(maxsize=None)
def glyph_length(word):
    return len(eva_glyphs(word))


@lru_cache(maxsize=None)
def splits(word):
    glyphs = eva_glyphs(word)
    return tuple((''.join(glyphs[:i]), ''.join(glyphs[i:])) for i in range(1, len(glyphs)))


def frequency_bin(count):
    return 0 if count == 0 else 1 if count == 1 else 2 if count <= 4 else 3 if count <= 19 else 4


def whole_hits(labels, words):
    return np.array([l['word'] in words.get(l['page'], ()) for l in labels], dtype=float)


def split_hits(labels, pairs):
    return np.array([any(s in pairs.get(l['page'], ()) for s in splits(l['word'])) for l in labels], dtype=float)


def permute_within_kind(labels, rng):
    by_kind = defaultdict(list)
    for i, label in enumerate(labels):
        by_kind[label['kind']].append(i)
    out = [dict(l) for l in labels]
    for ix in by_kind.values():
        for dest, src in zip(ix, rng.permutation(ix)):
            out[dest]['word'] = labels[int(src)]['word']
    return out


def permutation_test(labels, hits, table, seed, permutations=999):
    observed = float(hits(labels, table).mean())
    rng = np.random.default_rng(seed)
    null = np.array([hits(permute_within_kind(labels, rng), table).mean() for _ in range(permutations)])
    return dict(n=len(labels), observed=observed, null_mean=float(null.mean()), excess=observed-float(null.mean()),
                p=float((1 + np.sum(null >= observed))/(permutations + 1)))


def m1_length(label_types, counts, seed=3601, bootstrap=2000):
    pool = defaultdict(list)
    for word, count in counts.items():
        pool[frequency_bin(count)].append(glyph_length(word))
    reference = {b: float(np.mean(pool[max(b, 1)])) for b in range(5)}       # bin 0 compares with count-1 types
    diffs = np.array([glyph_length(w) - reference[frequency_bin(counts[w])] for w in label_types])
    rng = np.random.default_rng(seed)
    boots = [diffs[rng.integers(len(diffs), size=len(diffs))].mean() for _ in range(bootstrap)]
    by_bin = {}
    for b in range(5):
        chosen = [w for w in label_types if frequency_bin(counts[w]) == b]
        if chosen:
            by_bin[b] = dict(types=len(chosen), label_mean=float(np.mean([glyph_length(w) for w in chosen])),
                             reference_mean=reference[b])
    return dict(types=len(label_types), difference=float(diffs.mean()),
                interval=np.quantile(boots, [.025, .975]).tolist(), by_bin=by_bin,
                label_mean=float(np.mean([glyph_length(w) for w in label_types])))


def decomposable(word, pieces):
    return any(a in pieces and b in pieces for a, b in splits(word))


def m4_decomposability(label_types, counts, seed=3604, draws=999):
    pieces = {w for w, c in counts.items() if c >= PIECE_COUNT}
    chosen = sorted(w for w in label_types if glyph_length(w) >= MIN_GLYPHS)
    cells = defaultdict(list)
    for word, count in counts.items():
        cells[(glyph_length(word), frequency_bin(count))].append(word)
    for cell in cells.values():
        cell.sort()
    by_length = defaultdict(list)
    for (length, _), ws in cells.items():
        by_length[length].extend(ws)
    keys, fallbacks = [], 0
    for w in chosen:
        key = (glyph_length(w), max(frequency_bin(counts[w]), 1))
        if key not in cells:
            fallbacks += 1
        keys.append(key)
    observed = float(np.mean([decomposable(w, pieces) for w in chosen]))
    cache = {}
    flag = lambda w: cache.setdefault(w, decomposable(w, pieces))
    rng = np.random.default_rng(seed)
    control = []
    for _ in range(draws):
        total = 0
        for key in keys:
            options = cells.get(key) or sorted(by_length[key[0]])
            total += flag(options[int(rng.integers(len(options)))]) if options else 0
        control.append(total/len(keys))
    control = np.array(control)
    return dict(types=len(chosen), observed=observed, control_mean=float(control.mean()),
                excess=observed-float(control.mean()), fallbacks=fallbacks,
                p=float((1 + np.sum(control >= observed))/(draws + 1)))


def long_labels(labels):
    return [l for l in labels if glyph_length(l['word']) >= MIN_GLYPHS]


def calibrate(data):
    labels, long = data['labels'], long_labels(data['labels'])
    null = dict(M2=0, M3=0)
    power = {str(r): 0 for r in (.02, .05, .10)}
    for rep in range(20):
        rng = np.random.default_rng(3700 + rep)
        permuted = permute_within_kind(labels, rng)
        permuted_long = long_labels(permuted)
        null['M2'] += permutation_test(permuted, whole_hits, data['words'], 3800 + rep)['p'] < ALPHA
        null['M3'] += permutation_test(permuted_long, split_hits, data['pairs'], 3900 + rep)['p'] < ALPHA
        for r in (.02, .05, .10):
            pairs = {p: set(v) for p, v in data['pairs'].items()}
            chosen = rng.choice(len(permuted_long), size=max(1, round(r*len(permuted_long))), replace=False)
            for i in chosen:
                label = permuted_long[int(i)]
                glyphs = eva_glyphs(label['word'])
                half = len(glyphs)//2
                pairs.setdefault(label['page'], set()).add((''.join(glyphs[:half]), ''.join(glyphs[half:])))
            power[str(r)] += permutation_test(permuted_long, split_hits, pairs, 4000 + rep)['p'] < ALPHA
        print('calibration', rep, flush=True)
    null = {k: int(v) for k, v in null.items()}
    power = {k: int(v) for k, v in power.items()}
    detected = next((float(r) for r in ('0.02', '0.05', '0.1') if power[r] >= 16), None)
    return dict(null_fired=null, power_fired=power, total=20, smallest_detected_r=detected,
                gates=dict(M2=null['M2'] <= 2, M3=null['M3'] <= 2 and power['0.1'] >= 16))


def measures(data, labels):
    types = sorted({l['word'] for l in labels})
    return dict(labels=len(labels), types=len(types),
                M1=m1_length(types, data['counts']),
                M2=permutation_test(labels, whole_hits, data['words'], 3602),
                M3=permutation_test(long_labels(labels), split_hits, data['pairs'], 3603),
                M4=m4_decomposability(types, data['counts']))


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ZL, SPLIT, PROTOCOL]
    save(output/'manifest.json', dict(environment=environment(ROOT),
                                      hashes={str(p.relative_to(ROOT)): sha(p) for p in paths}))
    data = load()
    calibration = calibrate(data)
    save(output/'calibration.json', calibration)
    evidence = dict(status='structural diagnostic of label form; no meanings, no label/drawing alignment',
                    tally=dict(data['tally'], single_clean=len(data['labels']),
                               pages=len({l['page'] for l in data['labels']}),
                               running_tokens=sum(data['counts'].values()), running_types=len(data['counts'])),
                    alpha=ALPHA, gates=calibration['gates'], overall=measures(data, data['labels']))
    kinds = Counter(l['kind'] for l in data['labels'])
    evidence['by_kind'] = {}
    for kind, n in sorted(kinds.items()):
        chosen = [l for l in data['labels'] if l['kind'] == kind]
        types = sorted({l['word'] for l in chosen})
        long = long_labels(chosen)
        evidence['by_kind'][kind] = dict(
            labels=n, types=len(types), mean_length=float(np.mean([glyph_length(w) for w in types])),
            whole_recurrence=float(whole_hits(chosen, data['words']).mean()),
            split_recurrence=float(split_hits(long, data['pairs']).mean()) if long else None,
            in_running_text=float(np.mean([data['counts'][w] > 0 for w in types])))
    save(output/'evidence.json', evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/label_units_2026-10-10')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
