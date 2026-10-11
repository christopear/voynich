"""Preregistered test of n/l/r endings as added markers (stage 37).

Protocol: docs/protocols/ENDING_MARKERS_2026-10-10.md.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import json
from pathlib import Path
import re

import numpy as np

from voynich import mechanism_models as mm
from voynich.experiments.e06_boundary_frontier import load_lines
from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e28_word_homophones import save
from voynich.laboratory.manifest import environment
from voynich.laboratory.word_shapes import NGramModel
from voynich.paths import ROOT

ZL = ROOT/'data/ZL3b-n.txt'
IT = ROOT/'data/mechanisms/IT2a-n.txt'
SPLIT = ROOT/'results/image_annotation_pilot_2026-10-10/split.json'
PROTOCOL = ROOT/'docs/protocols/ENDING_MARKERS_2026-10-10.md'
NEIGHBOUR_GAPS = ('ordinary', 'uncertain')
GROUP = ('n', 'l', 'r')
COMPOUNDS = ('cth', 'ckh', 'cph', 'cfh', 'ch', 'sh')
COMMON = 5
ALPHA = .0125


@lru_cache(maxsize=None)
def glyphs(word):
    out, i = [], 0
    while i < len(word):
        hit = next((c for c in COMPOUNDS if word.startswith(c, i)), None)
        out.append(hit or word[i])
        i += len(hit) if hit else 1
    return tuple(out)


def stem(word):
    return ''.join(glyphs(word)[:-1])


def sealed_pages():
    sets = json.loads(SPLIT.read_text())['sets']
    return set(sets['confirmation_X']['pages']) | set(sets['confirmation_Y']['pages'])


def select(path, currier):
    """Paragraph lines of one Currier language, by ZL page labels, off the sealed pages."""
    labels = {ln['page']: ln['meta'].get('L') for ln in load_lines(ZL)}
    sealed = sealed_pages()
    return [ln for ln in load_lines(path) if labels.get(ln['page']) == currier and ln['page'] not in sealed]


def stream(lines):
    """Clean tokens with page and the next word's first glyph when it is a valid neighbour."""
    out = []
    for ln in lines:
        for i, token in enumerate(ln['words']):
            if not token['clean']:
                continue
            nxt = None
            if i < len(ln['gaps']) and ln['gaps'][i] in NEIGHBOUR_GAPS and ln['words'][i+1]['clean']:
                nxt = glyphs(ln['words'][i+1]['word'])[0]
            out.append(dict(page=ln['page'], word=token['word'], next=nxt))
    return out


def ending_table(tokens, counts, minimum=200):
    by = defaultdict(lambda: np.zeros(3))
    types = defaultdict(set)
    for t in tokens:
        g = glyphs(t['word'])
        if len(g) < 2:
            continue
        c = counts[stem(t['word'])]
        by[g[-1]] += (1, c >= 1, c >= COMMON)
        types[g[-1]].add(t['word'])
    out = {}
    for ending, (n, attested, common) in by.items():
        if n >= minimum:
            ts = types[ending]
            out[ending] = dict(tokens=int(n), attested=attested/n, common=common/n, types=len(ts),
                               type_attested=float(np.mean([counts[stem(w)] >= 1 for w in ts])),
                               type_common=float(np.mean([counts[stem(w)] >= COMMON for w in ts])))
    return dict(sorted(out.items(), key=lambda kv: -kv[1]['tokens']))


def m1(tokens, counts, group, *, bootstrap=2000, seed=3701):
    pages = defaultdict(lambda: np.zeros(6))        # group n, attested, common; other n, attested, common
    for t in tokens:
        g = glyphs(t['word'])
        if len(g) < 2:
            continue
        c = counts[stem(t['word'])]
        pages[t['page']][0 if g[-1] in group else 3:][:3] += (1, c >= 1, c >= COMMON)
    mass = np.array([pages[p] for p in sorted(pages)])

    def summary(index):
        s = mass[index].sum(axis=0)
        return s[2]/s[0], s[5]/s[3], s[1]/s[0], s[4]/s[3]

    group_common, other_common, group_attested, other_attested = summary(np.arange(len(mass)))
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(bootstrap):
        a, b, _, _ = summary(rng.integers(len(mass), size=len(mass)))
        boots.append(a-b)
    return dict(group_tokens=int(mass[:, 0].sum()), other_tokens=int(mass[:, 3].sum()),
                group_common=float(group_common), other_common=float(other_common),
                group_attested=float(group_attested), other_attested=float(other_attested),
                D=float(group_common-other_common), interval=np.quantile(boots, [.025, .975]).tolist())


def _conditional_mi(form, nxt, groups, nf, nn):
    total, n = 0., len(form)
    for ix in groups:
        joint = np.bincount(form[ix]*nn + nxt[ix], minlength=nf*nn).reshape(nf, nn).astype(float)
        rows, cols = joint.sum(axis=1, keepdims=True), joint.sum(axis=0, keepdims=True)
        mask = joint > 0
        total += (joint[mask]/n*np.log2(joint[mask]*len(ix)/(rows @ cols)[mask])).sum()
    return float(total)


def m2(tokens, group, *, permutations=999, seed=3702):
    bare, marked = defaultdict(list), defaultdict(list)
    for t in tokens:
        if t['next'] is None:
            continue
        g = glyphs(t['word'])
        bare[t['word']].append(t['next'])
        if len(g) >= 2 and g[-1] in group:
            marked[stem(t['word'])].append(t['next'])
    stems = sorted(s for s in marked if s in bare)
    form, nxt, key = [], [], []
    for i, s in enumerate(stems):
        for value in bare[s]:
            form.append(0); nxt.append(value); key.append(i)
        for value in marked[s]:
            form.append(1); nxt.append(value); key.append(i)
    if not stems:
        return dict(stems=0, records=0, raw=0., null_mean=0., excess=0., p=1.)
    table = {}
    nxt = np.array([table.setdefault(v, len(table)) for v in nxt])
    form, key = np.array(form), np.array(key)
    groups = [np.where(key == i)[0] for i in range(len(stems))]
    raw = _conditional_mi(form, nxt, groups, 2, len(table))
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(permutations):
        shuffled = nxt.copy()
        for ix in groups:
            shuffled[ix] = rng.permutation(nxt[ix])
        null.append(_conditional_mi(form, shuffled, groups, 2, len(table)))
    null = np.array(null)
    return dict(stems=len(stems), records=len(form), bare_records=int((form == 0).sum()),
                marked_records=int(form.sum()), raw=raw, null_mean=float(null.mean()), excess=raw-float(null.mean()),
                p=float((1 + np.sum(null >= raw))/(permutations + 1)))


def analyse(tokens, group=GROUP):
    counts = Counter(t['word'] for t in tokens)
    a, b = m1(tokens, counts, group), m2(tokens, group)
    return dict(tokens=len(tokens), types=len(counts), M1=a, M2=b,
                fires=bool(a['D'] > 0 and a['interval'][0] > 0 and b['p'] < ALPHA))


def shuffled_lines(lines, seed):
    """Permute clean words among clean positions within each page; layout and gaps are kept."""
    rng = np.random.default_rng(seed)
    slots = defaultdict(list)
    for li, ln in enumerate(lines):
        for wi, token in enumerate(ln['words']):
            if token['clean']:
                slots[ln['page']].append((li, wi))
    out = [dict(ln, words=[dict(w) for w in ln['words']]) for ln in lines]
    for positions in slots.values():
        words = [lines[li]['words'][wi]['word'] for li, wi in positions]
        for (li, wi), k in zip(positions, rng.permutation(len(words))):
            out[li]['words'][wi]['word'] = words[int(k)]
    return out


def plant(lines, kind, seed):
    rng = np.random.default_rng(seed)
    base = shuffled_lines(lines, seed + 50)
    tokens = stream(base)
    if kind == 'lexical':
        types = sorted({t['word'] for t in tokens if len(glyphs(t['word'])) >= 2})
        chosen = {types[int(i)] for i in rng.choice(len(types), size=round(.3*len(types)), replace=False)}
        for t in tokens:
            if t['word'] in chosen:
                t['word'] = stem(t['word']) + 'z'
        return tokens
    initials = sorted({t['next'] for t in tokens if t['next']})
    half = set(initials[::2])
    for t in tokens:
        p = .3 if kind == 'random' else (.6 if t['next'] in half else .05)
        if rng.random() < p:
            t['word'] = t['word'] + 'z'
    return tokens


def unattested(tokens, counts, cluster=False):
    def base(word):
        return re.sub(r'i*n$', '', word) if cluster and word.endswith('n') else stem(word)
    chosen = [t['word'] for t in tokens if len(glyphs(t['word'])) >= 2 and glyphs(t['word'])[-1] in GROUP]
    missing = Counter(w for w in chosen if counts[base(w)] == 0)
    common = sum(counts[base(w)] >= COMMON for w in chosen)
    return dict(tokens=len(chosen), never_attested_share=sum(missing.values())/len(chosen),
                common_share=common/len(chosen), never_attested_types=len(missing),
                commonest=[[w, n, base(w)] for w, n in missing.most_common(20)])


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT/'src/voynich/mechanism_models.py', ROOT/'src/voynich/laboratory/word_shapes.py',
             ZL, IT, SPLIT, PROTOCOL]
    save(output/'manifest.json', dict(environment=environment(ROOT),
                                      hashes={str(p.relative_to(ROOT)): sha(p) for p in paths}))
    lines = select(ZL, 'B')
    calibration = {}
    for kind in ('marker', 'random', 'lexical'):
        runs = [analyse(plant(lines, kind, 3800 + r), ('z',)) for r in range(10)]
        calibration[kind] = dict(fired=sum(r['fires'] for r in runs), total=10,
                                 D=[r['M1']['D'] for r in runs], M2_p=[r['M2']['p'] for r in runs])
        print('calibration', kind, calibration[kind]['fired'], flush=True)
    gate = calibration['marker']['fired'] >= 8 and calibration['random']['fired'] <= 1 and calibration['lexical']['fired'] <= 1
    save(output/'calibration.json', dict(kinds=calibration, gate_passed=gate))
    evidence = dict(status='structural test of endings as added markers; no readings', calibration_gate_passed=gate)
    if gate:
        tokens = stream(lines)
        counts = Counter(t['word'] for t in tokens)
        evidence['manuscript_B'] = analyse(tokens)
        evidence['endings'] = ending_table(tokens, counts)
        evidence['unattested'] = dict(single_glyph=unattested(tokens, counts), i_n_cluster=unattested(tokens, counts, True))
        evidence['IT2a_B'] = analyse(stream(select(IT, 'B')))
        evidence['ZL_A_non_sealed'] = analyse(stream(select(ZL, 'A')))
        words = [t['word'] for t in tokens]
        model, rng = NGramModel(words, 2), np.random.default_rng(3703)
        sampled = [dict(t, word=model.sample(rng)) for t in tokens]
        for i, t in enumerate(sampled[:-1]):
            if t['next'] is not None:
                t['next'] = glyphs(sampled[i+1]['word'])[0]
        evidence['glyph_chain_sample'] = analyse(sampled)
        generated, _ = mm.generate(mm.Training(lines), None, '', len(tokens), dict(mechanism='copy', level=2, coupling=1), 101)
        copied = [dict(t, word=w) for t, w in zip(tokens, generated)]
        for i, t in enumerate(copied[:-1]):
            if t['next'] is not None:
                t['next'] = glyphs(copied[i+1]['word'])[0]
        evidence['R2_coupled'] = analyse(copied)
    save(output/'evidence.json', evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/ending_markers_2026-10-10')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
