"""Post hoc corrective analyses for stages 35-38 (protocol CLAIMS_CORRECTION_2026-10-10.md).

Adds the calibrations the original claims lacked and the corrected stage-37
measures. Historical outputs and their producers are unchanged.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path

import numpy as np

from voynich import mechanism_models as mm
from voynich.experiments import e35_line_indicator as e35
from voynich.experiments import e36_label_units as e36
from voynich.experiments import e37_ending_markers as e37
from voynich.experiments import e38_word_parts as e38
from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e28_word_homophones import save
from voynich.laboratory.manifest import environment
from voynich.paths import ROOT

PROTOCOL = ROOT/'docs/protocols/CLAIMS_CORRECTION_2026-10-10.md'
TABLES = ROOT/'data/mechanisms/naibbe_tables.csv'
WEIGHTS = dict(alpha=28, beta1=14, beta2=11, beta3=11, gamma1=7, gamma2=7)


# ---------------------------------------------------------------- A: stage 38

def naibbe_tables():
    tables = defaultdict(lambda: defaultdict(dict))
    with TABLES.open(encoding='utf-8-sig') as stream:
        for row in csv.DictReader(stream):
            state, table, letter = row['code'].split('_')
            tables[table][state][letter] = row['glyphs']
    return tables


def simulate_naibbe(letters, names, one_draw, n_tokens, seed):
    """Naibbe-family simulation from Greshko's tables; not the published card procedure."""
    tables = naibbe_tables()
    rng = np.random.default_rng(seed)
    weights = np.array([WEIGHTS[n] for n in names], dtype=float)
    draw = lambda: names[int(rng.choice(len(names), p=weights/weights.sum()))]
    out, i = [], 0
    while len(out) < n_tokens and i < len(letters) - 1:
        if rng.random() < .5:
            out.append(tables[draw()]['unigram'][letters[i]])
            i += 1
        else:
            first = draw()
            second = first if one_draw else draw()
            out.append(tables[first]['prefix'][letters[i]] + tables[second]['suffix'][letters[i+1]])
            i += 2
    return out


def stage38_configurations():
    known = set(naibbe_tables()['alpha']['unigram'])
    texts = {}
    for name, path in (('latin', e38.LATIN), ('italian', e38.ITALIAN)):
        texts[name] = [c for c in mm.clean_plain(path.read_text()) if c in known]
    shuffled = list(texts['latin'])
    np.random.default_rng(4001).shuffle(shuffled)
    texts['latin_letters_shuffled'] = shuffled
    out = {}
    for text, letters in texts.items():
        for tables, names in (('six_tables', list(WEIGHTS)), ('alpha_only', ['alpha'])):
            for draws, one in (('separate_draws', False), ('one_draw_per_word', True)):
                if tables == 'alpha_only' and one:
                    continue                      # identical to separate draws with a single table
                words = simulate_naibbe(letters, names, one, 35000, 4002)
                result = e38.evaluate(e38.block_folds(words))
                out[f'{text}/{tables}/{draws}'] = dict(tokens=len(words), types=len(set(words)), T_new=result['T_new'],
                                                       mean_T_new=result['mean_T_new'], positive=result['positive'],
                                                       mean_coverage_new=result['mean_coverage_new'])
                print('A', text, tables, draws, round(result['mean_T_new'], 2), flush=True)
    return out


# ---------------------------------------------------------------- B: stage 35

def permute_endings(lines, seed):
    """Indicator lines get their final glyphs permuted among their own non-initial words."""
    counts = Counter(e35.eva_glyphs(ln['words'][0])[0] for ln in lines)
    upper, running = set(), 0
    for glyph in sorted(counts):
        if running >= sum(counts.values())/2:
            upper.add(glyph)
        running += counts[glyph]
    rng = np.random.default_rng(seed)
    out, changed, total = [], 0, 0
    for ln in lines:
        words = list(ln['words'])
        total += len(words) - 1
        if e35.eva_glyphs(words[0])[0] in upper:
            parts = [e35.eva_glyphs(w) for w in words[1:]]
            order = rng.permutation(len(parts))
            for i, j in enumerate(order):
                new = ''.join(parts[i][:-1] + [parts[int(j)][-1]])
                changed += parts[i][-1] != parts[int(j)][-1]
                words[i+1] = new
        out.append(dict(ln, words=words))
    return out, changed/total


def stage35_counterexample():
    b, _, _ = e35.load()
    runs = []
    for r in range(20):
        lines, share = permute_endings(e35.shuffle_first_words(b, 4100 + r), 4150 + r)
        result = e35.analyse(lines)
        runs.append(dict(share_of_endings_changed=share, D=result['D'], fires=result['fires']))
        print('B', r, round(share, 3), result['fires'], flush=True)
    return dict(fired=sum(r['fires'] for r in runs), total=20,
                mean_share_of_endings_changed=float(np.mean([r['share_of_endings_changed'] for r in runs])), runs=runs)


# ---------------------------------------------------------------- C: stage 36

def stage36_m2_power():
    data = e36.load()
    out = {}
    for r in (.02, .05, .10):
        fired, excess = 0, []
        for rep in range(20):
            rng = np.random.default_rng(4200 + rep)
            permuted = e36.permute_within_kind(data['labels'], rng)
            words = {p: set(v) for p, v in data['words'].items()}
            for i in rng.choice(len(permuted), size=max(1, round(r*len(permuted))), replace=False):
                label = permuted[int(i)]
                words.setdefault(label['page'], set()).add(label['word'])
            result = e36.permutation_test(permuted, e36.whole_hits, words, 4250 + rep)
            fired += result['p'] < e36.ALPHA
            excess.append(result['excess'])
        out[str(r)] = dict(fired=int(fired), total=20, mean_excess=float(np.mean(excess)))
        print('C', r, fired, flush=True)
    return out


# ---------------------------------------------------------------- D: stage 37

def m2_by_page(tokens, group, *, permutations=999, seed=4301):
    """M2 with next-initials permuted within stem and page; only cells holding both forms contribute."""
    cells = defaultdict(lambda: ([], []))
    words = {t['word'] for t in tokens}
    for t in tokens:
        if t['next'] is None:
            continue
        g = e37.glyphs(t['word'])
        if len(g) >= 2 and g[-1] in group and e37.stem(t['word']) in words:
            cells[(e37.stem(t['word']), t['page'])][1].append(t['next'])
        cells[(t['word'], t['page'])][0].append(t['next'])
    form, nxt, key = [], [], []
    kept = 0
    for bare, marked in cells.values():
        if bare and marked:
            form += [0]*len(bare) + [1]*len(marked)
            nxt += bare + marked
            key += [kept]*(len(bare) + len(marked))
            kept += 1
    if not kept:
        return dict(cells=0, records=0, raw=0., null_mean=0., excess=0., p=1.)
    table = {}
    nxt = np.array([table.setdefault(v, len(table)) for v in nxt])
    form, key = np.array(form), np.array(key)
    groups = [np.where(key == i)[0] for i in range(kept)]
    raw = e37._conditional_mi(form, nxt, groups, 2, len(table))
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(permutations):
        shuffled = nxt.copy()
        for ix in groups:
            shuffled[ix] = rng.permutation(nxt[ix])
        null.append(e37._conditional_mi(form, shuffled, groups, 2, len(table)))
    null = np.array(null)
    return dict(cells=kept, records=len(form), raw=raw, null_mean=float(null.mean()), excess=raw-float(null.mean()),
                p=float((1 + np.sum(null >= raw))/(permutations + 1)))


def page_confound(lines, seed):
    """`z` appended by page-level rate tied to the page's following-initial mix; no within-page dependence."""
    rng = np.random.default_rng(seed)
    tokens = e37.stream(e37.shuffled_lines(lines, seed + 50))
    half = set(sorted({t['next'] for t in tokens if t['next']})[::2])
    share = defaultdict(list)
    for t in tokens:
        if t['next']:
            share[t['page']].append(t['next'] in half)
    ranked = sorted(share, key=lambda p: (np.mean(share[p]), p))
    high = set(ranked[len(ranked)//2:])
    for t in tokens:
        if rng.random() < (.6 if t['page'] in high else .05):
            t['word'] = t['word'] + 'z'
    return tokens


def both_rules(tokens, group):
    counts = Counter(t['word'] for t in tokens)
    literal = Counter(t['word'] for t in tokens if len(e37.glyphs(t['word'])) >= 2)
    implemented, stated = e37.m1(tokens, counts, group), e37.m1(tokens, literal, group)
    pooled, paged = e37.m2(tokens, group), m2_by_page(tokens, group)
    ok = lambda m: m['D'] > 0 and m['interval'][0] > 0
    return dict(M1_as_implemented=implemented, M1_protocol_token_set=stated, M2_pooled=pooled, M2_by_page=paged,
                pooled_rule_fires=bool(ok(implemented) and pooled['p'] < e37.ALPHA),
                page_rule_fires=bool(ok(implemented) and paged['p'] < e37.ALPHA),
                page_rule_fires_protocol_token_set=bool(ok(stated) and paged['p'] < e37.ALPHA))


def stage37_corrections():
    lines = e37.select(e37.ZL, 'B')
    calibration = {}
    for kind in ('marker', 'random', 'lexical', 'page_confound'):
        runs = []
        for r in range(10):
            tokens = page_confound(lines, 4300 + r) if kind == 'page_confound' else e37.plant(lines, kind, 3800 + r)
            runs.append(both_rules(tokens, ('z',)))
        calibration[kind] = dict(pooled_rule_fired=sum(x['pooled_rule_fires'] for x in runs),
                                 page_rule_fired=sum(x['page_rule_fires'] for x in runs), total=10,
                                 pooled_p=[x['M2_pooled']['p'] for x in runs], page_p=[x['M2_by_page']['p'] for x in runs])
        print('D', kind, calibration[kind]['pooled_rule_fired'], calibration[kind]['page_rule_fired'], flush=True)
    gate = (calibration['marker']['page_rule_fired'] >= 8 and
            all(calibration[k]['page_rule_fired'] <= 1 for k in ('random', 'lexical', 'page_confound')))
    return dict(calibration=calibration, page_rule_gate_passed=gate,
                manuscript_B=both_rules(e37.stream(lines), e37.GROUP),
                IT2a_B=both_rules(e37.stream(e37.select(e37.IT, 'B')), e37.GROUP),
                ZL_A_non_sealed=both_rules(e37.stream(e37.select(e37.ZL, 'A')), e37.GROUP))


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    src = ROOT/'src/voynich/experiments'
    paths = [Path(__file__), src/'e35_line_indicator.py', src/'e36_label_units.py', src/'e37_ending_markers.py',
             src/'e38_word_parts.py', ROOT/'src/voynich/laboratory/word_parts.py', TABLES, e38.LATIN, e38.ITALIAN,
             e37.ZL, e37.IT, e37.SPLIT, PROTOCOL]
    save(output/'manifest.json', dict(environment=environment(ROOT),
                                      hashes={str(p.relative_to(ROOT)): sha(p) for p in paths}))
    evidence = dict(status='post hoc corrective calibrations and measures for stages 35-38; no readings')
    evidence['stage38_naibbe_family'] = stage38_configurations()
    evidence['stage35_distribution_preserving_indicator'] = stage35_counterexample()
    evidence['stage36_m2_power'] = stage36_m2_power()
    evidence['stage37'] = stage37_corrections()
    save(output/'evidence.json', evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/claims_correction_2026-10-10')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
