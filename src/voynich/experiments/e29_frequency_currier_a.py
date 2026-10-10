"""Additive frequency decomposition and matched herbal A/B panels (stage 29)."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

import numpy as np

from voynich.cipher_families import encode
from voynich.experiments.e06_boundary_frontier import load_lines
from voynich.experiments.e27_unit_association import association, sha, strata_indices
from voynich.experiments.e28_word_homophones import save
from voynich.laboratory.manifest import environment
from voynich.paths import ROOT

BINS = ('singleton', 'count2to4', 'count5plus')
SEED = 2901


def decomposition(tokens, rows, condition='section', *, seed=SEED, permutations=199):
    """Return additive MI contributions, in bits per original (not subset) token.

    Global frequency groups are invariant to the null permutations. Computing
    MI on each subset separately would measure a different quantity.
    """
    if not tokens or len(tokens) != len(rows) or permutations < 2:
        raise ValueError('aligned nonempty tokens/rows and >=2 permutations required')
    if condition not in ('section', 'roles'):
        raise ValueError('unknown condition')
    a, b = encode(tokens), encode([r['page'] for r in rows])
    n, nv, npages = len(a), int(a.max()) + 1, int(b.max()) + 1
    counts = np.bincount(a, minlength=nv)
    bins = np.where(counts == 1, 0, np.where(counts <= 4, 1, 2))
    keys = [r['section'] if condition == 'section' else
            (r['section'], tuple(r['roles'])) for r in rows]
    strata = strata_indices(keys)

    def contributions(words):
        result = np.zeros(3)
        for ix in strata:
            joint = np.bincount(words[ix] * npages + b[ix], minlength=nv*npages).reshape(nv, npages)
            w, p = np.nonzero(joint)
            value = joint[w, p]
            pieces = value/n * np.log2(value * len(ix) /
                                      (joint.sum(axis=1)[w] * joint.sum(axis=0)[p]))
            result += np.bincount(bins[w], weights=pieces, minlength=3)
        return result

    observed = contributions(a)
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(permutations):
        shuffled = a.copy()
        for ix in strata:
            shuffled[ix] = rng.permutation(a[ix])
        null.append(contributions(shuffled))
    null = np.asarray(null)

    def summary(raw, values):
        mean, sd = float(np.mean(values)), float(np.std(values, ddof=1))
        return dict(raw=float(raw), null_mean=mean, excess=float(raw)-mean,
                    null_sd=sd, null_mean_mcse=sd/np.sqrt(permutations),
                    null_interval=np.quantile(values, [.025, .975]).tolist())

    result = {name: {**summary(observed[i], null[:, i]),
                     'types': int(np.sum(bins == i)),
                     'token_mass': float(counts[bins == i].sum()/n)}
              for i, name in enumerate(BINS)}
    return dict(bins=result, total=summary(observed.sum(), null.sum(axis=1)),
                n=n, permutations=permutations, seed=seed)


def extract_pages(lines, allowed, join=False):
    """Use ZL classifications, including for IT; never rewrite Currier metadata."""
    pages = defaultdict(list)
    for line in lines:
        if line['page'] not in allowed:
            continue
        i = 0
        while i < len(line['words']):
            if not line['words'][i]['clean']:
                i += 1
                continue
            start = i
            word = line['words'][i]['word']
            while (join and i < len(line['gaps']) and line['gaps'][i] == 'uncertain'
                   and line['words'][i+1]['clean']):
                i += 1
                word += line['words'][i]['word']
            pages[line['page']].append(dict(word=word, page=line['page'], folio=line['folio'],
                section='H', currier=allowed[line['page']], locus=line['locus'], start=start, end=i,
                roles=(start == 0, i == len(line['words'])-1, line['paragraph_start'])))
            i += 1
    return pages


def manuscript_panels():
    zl = load_lines(ROOT/'data/ZL3b-n.txt')
    it = load_lines(ROOT/'data/mechanisms/IT2a-n.txt')
    allowed = {ln['page']: ln['meta'].get('L') for ln in zl
               if ln['meta'].get('I') == 'H' and ln['meta'].get('L') in ('A', 'B')}
    arms = {f'{tr}_{spacing}': extract_pages(lines, allowed, spacing == 'join')
            for tr, lines in [('ZL', zl), ('IT', it)] for spacing in ('split', 'join')}
    panels = {}
    for currier in ('A', 'B'):
        selected, seen = [], set()
        for page, rows in arms['ZL_split'].items():
            if allowed[page] != currier or rows[0]['folio'] in seen:
                continue
            if min(len(pages.get(page, [])) for pages in arms.values()) < 64:
                continue
            selected.append(page)
            seen.add(rows[0]['folio'])
            if len(selected) == 16:
                break
        if len(selected) != 16:
            raise ValueError(f'Only {len(selected)} eligible {currier} folios')
        for arm, pages in arms.items():
            for subset, choices in [('full', selected), ('early', selected[:8]), ('late', selected[8:])]:
                panels[f'{currier}_{arm}_{subset}'] = [r for p in choices for r in pages[p][:64]]
    return panels


def calibration():
    rows = [dict(page=str(i//64), section='H', roles=(i % 8 == 0, i % 8 == 7, i % 64 < 8))
            for i in range(1024)]
    rng = np.random.default_rng(SEED)
    iid, planted = [], []
    for seed in range(50):
        tokens = [str(x) for x in rng.integers(128, size=1024)]
        result = decomposition(tokens, rows, seed=seed)
        iid.append(result['total']['excess'])
        if seed == 0:
            for condition in ('section', 'roles'):
                measured = decomposition(tokens, rows, condition, seed=seed)
                scalar = association(tokens, rows, condition, seed=seed)
                for key in ('raw', 'null_mean', 'excess'):
                    assert abs(measured['total'][key]-scalar[key]) < 1e-10
                renamed = decomposition(['code'+t for t in tokens], rows, condition, seed=seed)
                assert measured == renamed
    for seed in range(10):
        tokens = [f'p{i//64}w{i%16}' for i in range(1024)]
        result = decomposition(tokens, rows, seed=seed)
        planted.append(result['total']['excess'])
        assert abs(result['bins']['count2to4']['excess']-result['total']['excess']) < 1e-10
    unique = decomposition([str(i) for i in range(1024)], rows)
    assert abs(unique['total']['excess']) < 1e-10
    assert abs(np.mean(iid)) < .01 and np.mean(planted) > .2
    return dict(iid=iid, iid_mean=float(np.mean(iid)), planted=planted,
                planted_mean=float(np.mean(planted)), unique=unique, passed=True)


def measure(tokens, rows):
    counts = Counter(tokens)
    return dict(section=decomposition(tokens, rows), roles=decomposition(tokens, rows, 'roles'),
                ttr=len(counts)/len(tokens), top10=sum(v for _, v in counts.most_common(10))/len(tokens))


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    save(output/'calibration.json', calibration())
    panels = manuscript_panels()
    previous = ROOT/'results/word_homophones_2026-10-09'
    old = json.loads((previous/'slots.json').read_text())
    panels.update({'previous_'+name: rows for name, rows in old.items()})
    save(output/'slots.json', panels)
    results = {}
    for name, rows in panels.items():
        results[name] = measure([r['word'] for r in rows], rows)
        print(name, results[name]['section']['total']['excess'], flush=True)
    sources = json.loads((previous/'source_panels.json').read_text())
    reference = {}
    for source, passages in sources.items():
        for passage in passages:
            layout = old['ZL_original'] if passage['split'] == 'development' else old['ZL_additional']
            reference[f"{source}_{passage['split']}_{passage['seed']}"] = measure(passage['words'], layout)
    paths = [Path(__file__), ROOT/'data/ZL3b-n.txt', ROOT/'data/mechanisms/IT2a-n.txt',
             previous/'slots.json', previous/'source_panels.json',
             ROOT/'docs/protocols/FREQUENCY_CURRIER_A_2026-10-09.md']
    save(output/'manifest.json', dict(environment=environment(ROOT),
        hashes={str(p.relative_to(ROOT)): sha(p) for p in paths}))
    save(output/'evidence.json', dict(manuscript=results, reference=reference,
        status='Descriptive structural diagnostic; no readings or cipher-family rejection'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/frequency_currier_a_2026-10-09')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
