"""Frozen unit-size/page-association study. See UNIT_ASSOCIATION_2026-10-09.md."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from voynich.acquisition.unit_sources import SOURCE, sources
from voynich.cipher_families import encode, mi_codes
from voynich.experiments.e06_boundary_frontier import load_lines
from voynich.laboratory.manifest import environment
from voynich.paths import ROOT
from voynich.slot_cipher import syllabify
from voynich.voynich_core import eva_glyphs

PERMUTATIONS = 199
KINDS = ('letter', 'pair', 'syllable', 'word', 'mixed50', 'mixed200')
SEEDS = (7, 19, 31)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def page_tokens(lines, join=False):
    pages = defaultdict(list)
    for line in lines:
        if line['meta'].get('L') != 'B' or line['meta'].get('I') not in {'B', 'H'}:
            continue
        i = 0
        while i < len(line['words']):
            if not line['words'][i]['clean']:
                i += 1
                continue
            start = i
            word = line['words'][i]['word']
            while (join and i < len(line['gaps']) and line['gaps'][i] == 'uncertain'
                   and line['words'][i + 1]['clean']):
                i += 1
                word += line['words'][i]['word']
            pages[line['page']].append(dict(word=word, page=line['page'], folio=line['folio'],
                section=line['meta']['I'], locus=line['locus'], start=start, end=i,
                roles=(start == 0, i == len(line['words']) - 1, line['paragraph_start'])))
            i += 1
    return pages


def manuscript():
    lines = load_lines(ROOT / 'data/ZL3b-n.txt')
    split, joined = page_tokens(lines), page_tokens(lines, True)
    chosen, folios, counts = [], set(), Counter()
    for page, rows in split.items():
        section, folio = rows[0]['section'], rows[0]['folio']
        if folio in folios or counts[section] >= 8:
            continue
        if min(len(rows), len(joined[page])) < 64:
            continue
        chosen.append(page); folios.add(folio); counts[section] += 1
    if counts != {'H': 8, 'B': 8}:
        raise ValueError(f'Insufficient eligible pages: {counts}')
    return {arm: [r for page in chosen for r in panels[page][:64]]
            for arm, panels in [('split', split), ('join', joined)]}


def strata_indices(values):
    groups = defaultdict(list)
    for i, value in enumerate(values):
        groups[value].append(i)
    return [np.array(indices) for indices in groups.values()]


def conditional_mi(a, b, strata):
    return sum(len(ix) / len(a) * mi_codes(a[ix], b[ix]) for ix in strata)


def association(tokens, rows, condition='section', *, cap=None, seed=0, permutations=PERMUTATIONS,
                block=False):
    tokens = list(tokens)
    if cap is not None:
        # Counter preserves first occurrence for frequency ties. Sentinel cannot collide.
        common = {v for v, _ in Counter(tokens).most_common(cap)}
        tokens = [(0, v) if v in common else (1, '') for v in tokens]
    a, b = encode(tokens), encode([r['page'] for r in rows])
    keys = [None if condition == 'pooled' else r['section'] if condition == 'section'
            else (r['section'], tuple(r['roles'])) for r in rows]
    strata = strata_indices(keys)
    observed = conditional_mi(a, b, strata)
    rng = np.random.default_rng(seed)
    nulls = []
    for _ in range(permutations):
        shuffled = a.copy()
        for ix in strata:
            if block:
                if len(ix) % 8:
                    raise ValueError('Block permutation requires multiples of eight')
                blocks = a[ix].reshape(-1, 8)
                shuffled[ix] = blocks[rng.permutation(len(blocks))].ravel()
            else:
                shuffled[ix] = rng.permutation(a[ix])
        nulls.append(conditional_mi(shuffled, b, strata))
    mean = float(np.mean(nulls)); sd = float(np.std(nulls, ddof=1))
    return dict(raw=observed, null_mean=mean, excess=observed-mean, null_sd=sd,
                null_mean_mcse=sd/math.sqrt(permutations), permutations=permutations)


def measurements(tokens, rows, seed=0):
    result = {}
    for cap, label in [(None, 'all'), (200, 'top200')]:
        for condition in ('pooled', 'section', 'roles'):
            result[f'{label}_{condition}'] = association(tokens, rows, condition, cap=cap, seed=seed)
    result['all_section_blocks8'] = association(tokens, rows, seed=seed, block=True)
    for section in ('H', 'B'):
        ix = [i for i, r in enumerate(rows) if r['section'] == section]
        result[f'all_{section}'] = association([tokens[i] for i in ix], [rows[i] for i in ix], seed=seed)
    counts = Counter(tokens)
    adjacent = [(i-1, i) for i in range(1, len(rows)) if rows[i]['locus'] == rows[i-1]['locus']
                and rows[i]['start'] == rows[i-1]['end'] + 1]
    result['shape'] = dict(tokens=len(tokens), vocabulary=len(counts), ttr=len(counts)/len(tokens),
        hapax_type_share=sum(n == 1 for n in counts.values())/len(counts),
        top10_share=sum(n for _, n in counts.most_common(10))/len(tokens),
        adjacent_repeat_rate=sum(tokens[a] == tokens[b] for a, b in adjacent)/max(1, len(adjacent)),
        measured_adjacencies=len(adjacent))
    return result


def units(words, kind, dictionary=()):
    out = []
    for word in words:
        if kind == 'word' or (kind.startswith('mixed') and word in dictionary):
            out.append('w:' + word)
        elif kind == 'pair':
            out.extend('p:' + word[i:i+2] for i in range(0, len(word), 2))
        elif kind == 'syllable':
            out.extend('s:' + part for part in syllabify(word))
        else:
            out.extend('l:' + c for c in word)
    return out


def source_panels(chapters, seed):
    eligible = [c for c in chapters if len(c['words']) >= 64]
    n_train = max(1, len(eligible)//5)
    training, available = eligible[:n_train], eligible[n_train:]
    dictionary = [w for w, _ in Counter(w for c in training for w in c['words']).most_common(200)]
    rng = np.random.default_rng(seed)
    selected = [available[i] for i in rng.choice(len(available), 16, replace=False)]
    panels = []
    for kind in KINDS:
        tokens, spans = [], []
        limit = int(kind[5:]) if kind.startswith('mixed') else 0
        for chapter in selected:
            stream = units(chapter['words'], kind, set(dictionary[:limit]))
            offset = int(rng.integers(len(stream) - 63))
            tokens += stream[offset:offset+64]
            spans.append(dict(chapter=chapter['id'], unit_start=offset, unit_stop=offset+64))
        panels.append(dict(kind=kind, seed=seed, tokens=tokens, spans=spans,
                           dictionary=dictionary[:limit], training_ids=[c['id'] for c in training]))
    return panels


def calibration(rows):
    records = []
    for mode, trials in [('iid', 50), ('planted', 10)]:
        for seed in range(trials):
            rng = np.random.default_rng(9000+seed)
            tokens = [str(int(rng.integers(32))) for _ in rows]
            if mode == 'planted':
                tokens = [r['page'] + ':' + t if rng.random() < .5 else t for r, t in zip(rows, tokens)]
            records.append(dict(mode=mode, seed=seed, **association(tokens, rows, seed=seed)))
    means = {mode: float(np.mean([r['excess'] for r in records if r['mode'] == mode]))
             for mode in ('iid', 'planted')}
    if abs(means['iid']) > .02 or means['planted'] <= .1:
        raise AssertionError(f'Calibration gate failed: {means}')
    return dict(records=records, means=means, passed=True)


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    arms = manuscript(); rows = arms['split']
    corpus = sources()
    files = [ROOT/'data/ZL3b-n.txt', ROOT/'data/latin_alfonsi.txt', ROOT/'data/italian_dante.txt',
             ROOT/'docs/protocols/UNIT_ASSOCIATION_2026-10-09.md', Path(__file__),
             ROOT/'src/voynich/acquisition/unit_sources.py', ROOT/'src/voynich/slot_cipher.py',
             ROOT/'src/voynich/experiments/e06_boundary_frontier.py'] + sorted(SOURCE.glob('*'))
    dump(output/'manifest.json', dict(files={str(p.relative_to(ROOT)): sha(p) for p in files if p.is_file()},
        environment=environment(ROOT), source_chapter_hashes={name: hashlib.sha256(
            json.dumps(chapters, sort_keys=True).encode()).hexdigest() for name, chapters in corpus.items()}))
    dump(output/'prepared_sources.json', corpus)
    dump(output/'manuscript_slots.json', arms)
    checks = calibration(rows); dump(output/'calibration.json', checks)
    print('Calibration passed', checks['means'], flush=True)
    results = []
    for arm, slots in arms.items():
        tokens = [r['word'] for r in slots]
        results.append(dict(id=f'voynich-{arm}', kind='manuscript', tokens=tokens,
                            metrics=measurements(tokens, slots)))
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        tokens = [r['word'] for r in rows]
        shuffled = tokens.copy()
        for ix in strata_indices([(r['section'], tuple(r['roles'])) for r in rows]):
            for i, value in zip(ix, rng.permutation([tokens[i] for i in ix])):
                shuffled[i] = str(value)
        results.append(dict(id=f'word-shuffle-{seed}', kind='control', tokens=shuffled,
                            metrics=measurements(shuffled, rows)))
        shuffled = []
        for start in range(0, len(rows), 64):
            chunks = [eva_glyphs(t) for t in tokens[start:start+64]]
            glyphs = rng.permutation([g for chunk in chunks for g in chunk]).tolist()
            pos = 0
            for chunk in chunks:
                shuffled.append(''.join(glyphs[pos:pos+len(chunk)])); pos += len(chunk)
        results.append(dict(id=f'glyph-shuffle-{seed}', kind='control', tokens=shuffled,
                            metrics=measurements(shuffled, rows)))
    for name, chapters in corpus.items():
        for seed in SEEDS:
            for panel in source_panels(chapters, seed):
                panel.update(id=f"{name}-{panel['kind']}-{seed}", source=name,
                             metrics=measurements(panel['tokens'], rows))
                results.append(panel)
            print(name, seed, 'complete', flush=True)
    dump(output/'evidence.json', dict(results=results, protocol='UNIT_ASSOCIATION_2026-10-09.md'))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/unit_association_2026-10-09')
    args = parser.parse_args()
    run(args.output)


if __name__ == '__main__':
    main()
