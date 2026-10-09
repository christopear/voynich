"""Preregistered scribe control, dependent word-shape models and conditional codebooks (stage 31)."""
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
from voynich.experiments.e30_structured_word_codes import R2, profile as stage30_profile, training_lines
from voynich.laboratory.manifest import environment
from voynich.laboratory.structured_codes import RULES, SlotGrammar, serialized_bits
from voynich.laboratory.word_shapes import (
    NGramModel, coupling, folio_cv, model_codebook, page_hands, scribe_measure, shape_diagnostics,
    stratified_decomposition,
)
from voynich.paths import ROOT
from voynich.voynich_core import eva_glyphs

NAMES = ['ttr', 'top10', 'section_excess', 'role_excess', 'frequent_excess', 'mean_length', 'glyph_h', 'coupling']
SCALES = np.array([.05, .04, .05, .05, .05, .5, .25, .05])
TARGETS = ('B_ZL_split_early', 'B_ZL_split_late', 'B_IT_split_late', 'B_ZL_join_late', 'A_ZL_split_late')
EVALUATION = TARGETS[1:]
ORDERS = (1, 2, 3)
K_VALUES = (2968, 14336)
SAMPLE_SEEDS = range(3201, 3221)
GATE = dict(glyph_h=.25, d_last=.25, mean_length=.5, coverage=.549)
ZL = ROOT/'data/ZL3b-n.txt'
STAGE29 = ROOT/'results/frequency_currier_a_2026-10-09/slots.json'
STAGE28 = ROOT/'results/word_homophones_2026-10-09/source_panels.json'
PREPARED = ROOT/'results/unit_association_2026-10-09/prepared_sources.json'
PROTOCOL = ROOT/'docs/protocols/WORD_SHAPES_2026-10-09.md'


# ---------------------------------------------------------------- Part A

def calibration_a(hand_sequence):
    """Synthetic 16-page layout with the B_ZL_split_full hand order."""
    pages = [str(i) for i in range(16)]
    hands = dict(zip(pages, hand_sequence))
    rows = [dict(page=str(i//64), section='H', roles=(i % 8 == 0, i % 8 == 7, i % 64 < 8)) for i in range(1024)]
    hand_ids = sorted(set(hand_sequence))
    out = dict(iid=[], hand=[], page=[])
    for seed in range(20):
        rng = np.random.default_rng(seed)
        iid = [str(x) for x in rng.integers(128, size=1024)]
        by_hand = [f"h{hands[r['page']]}w{rng.integers(64)}" for r in rows]
        by_page = [f"p{r['page']}w{rng.integers(16)}" for r in rows]
        for name, tokens in (('iid', iid), ('hand', by_hand), ('page', by_page)):
            plain = stratified_decomposition(tokens, rows, [r['section'] for r in rows], seed=seed)
            within = stratified_decomposition(tokens, rows, [(r['section'], hands[r['page']]) for r in rows], seed=seed)
            out[name].append([plain['total']['excess'], within['total']['excess']])
    mean = {k: np.mean(v, axis=0).tolist() for k, v in out.items()}
    checks = dict(iid=max(abs(mean['iid'][0]), abs(mean['iid'][1])) < .01,
                  hand=mean['hand'][0] > .1 and abs(mean['hand'][1]) < .02,
                  page=mean['page'][1] >= .8*mean['page'][0])
    same = dict.fromkeys(pages, '1')
    tokens = [str(x) for x in np.random.default_rng(99).integers(64, size=1024)]
    equal = stratified_decomposition(tokens, rows, [r['section'] for r in rows]) == \
        stratified_decomposition(tokens, rows, [(r['section'], same[r['page']]) for r in rows])
    checks['single_hand_identity'] = equal
    return dict(hand_ids=hand_ids, draws=out, means=mean, checks=checks, passed=all(checks.values()))


def part_a(slots, hands, sources):
    full = slots['B_ZL_split_full']
    hand_sequence = [hands[p] for p in dict.fromkeys(r['page'] for r in full)]
    calibration = calibration_a(hand_sequence)
    manuscript = {name: scribe_measure([r['word'] for r in rows], rows, hands) for name, rows in slots.items()}
    reference = {f"{source}_{p['split']}_{p['seed']}": scribe_measure(p['words'], full, hands)
                 for source, passages in sources.items() for p in passages}
    shares = [v['section_retained_share'] for v in reference.values() if v['section_retained_share'] is not None]
    b = manuscript['B_ZL_split_full']['section_retained_share']
    return dict(calibration=calibration, manuscript=manuscript, reference=reference,
                reference_min_retained_share=min(shares), B_ZL_split_full_retained_share=b,
                B_below_all_references=bool(b < min(shares)))


# ---------------------------------------------------------------- Part B

class SlotShape:
    """Stage-30 slot grammar exposed through the Part B model interface."""

    def __init__(self, words):
        self.grammar = SlotGrammar.fit(words)
        self.codes = list(self.grammar.weights)
        weights = np.array(list(self.grammar.weights.values()), dtype=float)
        self.p = weights/weights.sum()
        self.lookup = dict(zip(self.codes, self.p))

    def sample(self, rng):
        return self.codes[int(rng.choice(len(self.codes), p=self.p))]

    def top(self, k):
        ranked = sorted(self.lookup.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
        return [(w, float(np.log2(p))) for w, p in ranked]

    def covered_cross_entropy(self, words):
        covered = [w for w in words if w in self.lookup]
        bits = -sum(np.log2(self.lookup[w]) for w in covered)
        return float(bits/sum(len(eva_glyphs(w))+1 for w in covered)) if covered else None


def broad_lines(reserved_folios):
    return [ln for ln in load_lines(ZL) if ln['meta'].get('L') == 'B' and ln['folio'] not in reserved_folios]


def coverage(top, tokens, seen):
    support = set(top)
    types, unseen = set(tokens), set(tokens) - set(seen)
    return dict(size=len(support), token=sum(w in support for w in tokens)/len(tokens),
                type=sum(w in support for w in types)/len(types), unseen_types=len(unseen),
                unseen_type=sum(w in support for w in unseen)/len(unseen) if unseen else None)


def samples(model, seeds=SAMPLE_SEEDS, n=512):
    out = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        out.append([model.sample(rng) for _ in range(n)])
    return out


def summarize(diagnostics):
    keys = diagnostics[0].keys()
    return {k: dict(median=float(np.median([d[k] for d in diagnostics])),
                    min=float(min(d[k] for d in diagnostics)), max=float(max(d[k] for d in diagnostics)))
            for k in keys}


def part_b(arms, targets):
    observed = {name: shape_diagnostics([r['word'] for r in rows]) for name, rows in targets.items()}
    result = dict(observed=observed, arms={})
    models = {}
    for arm, by_folio in arms.items():
        words = [w for ws in by_folio.values() for w in ws]
        seen = set(words)
        cv = {order: folio_cv(by_folio, order) for order in ORDERS}
        selected = min(ORDERS, key=lambda o: (cv[o], o))
        arm_models = {'S0': SlotShape(words), **{f'N{o}': NGramModel(words, o) for o in ORDERS}}
        models[arm] = arm_models
        frequent = [w for w, _ in sorted(Counter(words).items(), key=lambda kv: (-kv[1], kv[0]))]
        record = dict(tokens=len(words), types=len(seen), folios=len(by_folio), cv=cv,
                      selected=f'N{selected}', models={},
                      memorisation={str(k): {t: coverage(frequent[:k], [r['word'] for r in rows], seen)
                                             for t, rows in targets.items() if t in EVALUATION} for k in K_VALUES})
        for name, model in arm_models.items():
            drawn = samples(model)
            entry = dict(samples=summarize([shape_diagnostics(s) for s in drawn]), coverage={}, cross_entropy={})
            tops = {k: [w for w, _ in model.top(k)] for k in K_VALUES}
            for target in EVALUATION:
                tokens = [r['word'] for r in targets[target]]
                entry['coverage'][target] = {str(k): coverage(tops[k], tokens, seen) for k in K_VALUES}
                if name == 'S0':
                    entry['cross_entropy'][target] = dict(
                        covered_tokens_only=model.covered_cross_entropy(tokens),
                        note='Zero probability outside support; not comparable with n-gram values.')
                else:
                    entry['cross_entropy'][target] = dict(token=model.cross_entropy(tokens),
                                                          type=model.cross_entropy(sorted(set(tokens))))
            if name == 'S0':
                entry['grammar'] = dict(unique_support=len(model.codes), combinations=model.grammar.combinations)
            else:
                entry['serialization_bits'] = serialized_bits(model.description())
            entry['sample_words'] = drawn[0][:64]
            record['models'][name] = entry
        chosen = record['models'][record['selected']]
        primary = observed['B_ZL_split_late']
        residuals = dict(glyph_h=chosen['samples']['glyph_h']['median']-primary['glyph_h'],
                         d_last=chosen['samples']['d_last']['median']-primary['d_last'],
                         mean_length=chosen['samples']['mean_length']['median']-primary['mean_length'])
        cover = chosen['coverage']['B_ZL_split_late']['2968']['token']
        checks = {k: abs(v) <= GATE[k] for k, v in residuals.items()}
        checks['coverage'] = cover >= GATE['coverage']
        record['gate'] = dict(residuals=residuals, coverage=cover, checks=checks, passed=all(checks.values()))
        result['arms'][arm] = record
        print('part B', arm, record['selected'], record['gate'], flush=True)
    return result, models


# ---------------------------------------------------------------- Part C

def profile(tokens, rows):
    out = stage30_profile(tokens, rows)
    out['coupling'] = coupling(tokens, rows)
    out['vector'] = out['vector'] + [out['coupling']['excess']]
    return out


def distance(a, b):
    return float(np.max(np.abs(np.array(a)-np.array(b))/SCALES))


def medians(records, family):
    out = {}
    for setting in sorted({r['setting'] for r in records if r['family'] == family}):
        values = [r['profile']['vector'] for r in records if r['family'] == family and r['setting'] == setting]
        out[setting] = np.median(values, axis=0).tolist()
    return out


def closest(vector, candidates):
    return min((dict(setting=s, distance=distance(vector, m), median=m) for s, m in candidates.items()),
               key=lambda r: (r['distance'], r['setting']))


def discrimination(records):
    predictions = []
    for record in records:
        remaining = [r for r in records if r['seed'] != record['seed']]
        scores = {f: closest(record['profile']['vector'], medians(remaining, f))['distance'] for f in ('cipher', 'R2')}
        predictions.append(dict(family=record['family'], setting=record['setting'], seed=record['seed'],
                                passage=record.get('passage'), prediction=min(scores, key=lambda f: (scores[f], f)),
                                distances=scores))
    accuracy = {f: sum(p['prediction'] == f for p in predictions if p['family'] == f) /
                sum(p['family'] == f for p in predictions) for f in ('cipher', 'R2')}
    return dict(by_family=accuracy, balanced_accuracy=sum(accuracy.values())/2,
                passed=sum(accuracy.values())/2 >= .8, predictions=predictions)


def part_c(output, arm, model, r2_lines, targets, hands):
    dev, val = targets['B_ZL_split_early'], targets['B_ZL_split_late']
    panels = [dict(p, words=p['words'][:512], spans=p['spans'][:8]) for p in json.loads(STAGE28.read_text())['cucina']]
    save(output/'source_panels.json', panels)
    vocabulary = sorted({w for ch in json.loads(PREPARED.read_text())['cucina'] for w in ch['words']})
    books, draws = {}, {}
    for seed in range(101, 107):
        books[seed], draws[seed] = model_codebook(vocabulary, model, seed)
    save(output/'codebooks.json', {seed: book.encode for seed, book in books.items()})
    train = mm.Training(r2_lines)
    save(output/'costs.json', dict(
        arm=arm, shape_model_serialization_bits=serialized_bits(model.description()),
        cipher={seed: dict(book.costs(), model_draws=draws[seed]) for seed, book in books.items()},
        R2_training_tokens=len(train.words),
        note='Explicit serialization/reference budgets, not comparable likelihoods or an MDL ranking.'))
    records = []
    for panel in panels:
        rows = dev if panel['split'] == 'development' else val
        for seed, book in books.items():
            for setting, rule in enumerate(RULES):
                tokens, audit = book.encrypt(panel['words'], [r['page'] for r in rows], rule,
                                            10000+100*panel['seed']+seed)
                assert book.decrypt(tokens) == panel['words']
                records.append(dict(family='cipher', split=panel['split'], setting=setting, rule=rule, seed=seed,
                                    passage=panel['seed'], tokens=tokens, audit=audit, profile=profile(tokens, rows)))
        print('cipher', panel['split'], panel['seed'], flush=True)
    for split, rows, seeds in [('development', dev, range(101, 107)), ('validation', val, range(201, 207))]:
        for setting, config in enumerate(R2):
            for seed in seeds:
                tokens, audit = mm.generate(train, None, '', 512, config, seed)
                records.append(dict(family='R2', split=split, setting=setting, config=config, seed=seed,
                                    tokens=tokens, audit=audit, profile=profile(tokens, rows)))
        print('R2', split, flush=True)
    save(output/'generated.json', records)
    development = [r for r in records if r['split'] == 'development']
    candidates = medians(development, 'cipher')
    calibration = []
    for key_seed in (701, 702):
        book, _ = model_codebook(vocabulary, model, key_seed)
        for panel in [p for p in panels if p['split'] == 'development']:
            for rule in RULES:
                tokens, _ = book.encrypt(panel['words'], [r['page'] for r in dev], rule,
                                        10000+100*panel['seed']+key_seed)
                assert book.decrypt(tokens) == panel['words']
                measured = profile(tokens, dev)
                calibration.append(dict(key_seed=key_seed, passage=panel['seed'], rule=rule, profile=measured,
                                        selected=closest(measured['vector'], candidates)))
    passed = sum(c['selected']['distance'] <= 2 for c in calibration)
    calibrated = dict(passed=passed, total=16, gate=12, records=calibration, discrimination=discrimination(development))
    save(output/'calibration.json', calibrated)
    if passed < 12:
        return dict(status='calibration failed; manuscript profile comparison stopped', calibration_passed=passed)
    measured_targets = {name: dict(profile=profile([r['word'] for r in rows], rows),
                                   hand_section=stratified_decomposition(
                                       [r['word'] for r in rows], rows, [(r['section'], hands[r['page']]) for r in rows]))
                        for name, rows in targets.items()}
    target = measured_targets['B_ZL_split_early']['profile']['vector']
    selection = {f: closest(target, medians(development, f)) for f in ('cipher', 'R2')}
    comparisons = {}
    for family, chosen in selection.items():
        comparisons[family] = {}
        for name, observed in measured_targets.items():
            split = 'development' if name.endswith('early') else 'validation'
            values = []
            for record in records:
                if (record['family'], record['setting'], record['split']) != (family, chosen['setting'], split):
                    continue
                rows = targets[name]
                measured = record['profile'] if name in ('B_ZL_split_early', 'B_ZL_split_late') else profile(record['tokens'], rows)
                hand = stratified_decomposition(record['tokens'], rows, [(r['section'], hands[r['page']]) for r in rows])
                values.append(dict(seed=record['seed'], passage=record.get('passage'), profile=measured,
                                   hand_section_excess=hand['total']['excess'],
                                   distance=distance(measured['vector'], observed['profile']['vector']),
                                   signed_residual=(np.array(measured['vector'])-observed['profile']['vector']).tolist()))
            comparisons[family][name] = dict(hits=sum(v['distance'] <= 1 for v in values), total=len(values), draws=values)
    return dict(status='descriptive forward-model screen; no key recovery or readings', arm=arm,
                names=NAMES, scales=SCALES.tolist(), targets=measured_targets, selection=selection,
                comparisons=comparisons, calibration_passed=passed,
                balanced_accuracy=calibrated['discrimination']['balanced_accuracy'])


# ---------------------------------------------------------------- run

def training_arms(targets):
    """Broad (all clean Currier B ZL tokens off the reserved folios) and matched (stage-30) arms by folio."""
    reserved = {r['folio'] for r in targets['B_ZL_split_late']}
    lines = broad_lines(reserved)
    broad = defaultdict(list)
    for ln in lines:
        broad[ln['folio']].extend(w['word'] for w in ln['words'] if w['clean'])
    matched = defaultdict(list)
    for r in targets['B_ZL_split_early']:
        matched[r['folio']].append(r['word'])
    return reserved, lines, {'broad': dict(broad), 'matched': dict(matched)}


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    slots = json.loads(STAGE29.read_text())
    hands = page_hands(ZL)
    sources = json.loads(STAGE28.read_text())
    paths = [Path(__file__), ROOT/'src/voynich/laboratory/word_shapes.py',
             ROOT/'src/voynich/laboratory/structured_codes.py', ROOT/'src/voynich/mechanism_models.py',
             ROOT/'src/voynich/experiments/e30_structured_word_codes.py', ZL, STAGE29, STAGE28, PREPARED, PROTOCOL]
    save(output/'manifest.json', dict(environment=environment(ROOT),
                                      hashes={str(p.relative_to(ROOT)): sha(p) for p in paths}))
    save(output/'hands.json', hands)

    scribe = part_a(slots, hands, sources)
    save(output/'scribe.json', scribe)
    print('part A calibration', scribe['calibration']['checks'], flush=True)

    targets = {name: slots[name] for name in TARGETS}
    save(output/'slots.json', targets)
    reserved, lines, arms = training_arms(targets)
    save(output/'training.json', dict(broad_folios=sorted(arms['broad']), reserved_folios=sorted(reserved),
                                      broad_tokens=sum(map(len, arms['broad'].values())),
                                      matched_folios=sorted(arms['matched'])))
    shapes, models = part_b(arms, targets)
    save(output/'shapes.json', shapes)

    if shapes['arms']['broad']['gate']['passed']:
        arm, r2_lines = 'broad', lines
    elif shapes['arms']['matched']['gate']['passed']:
        arm, r2_lines = 'matched', training_lines(targets['B_ZL_split_early'])
    else:
        save(output/'evidence.json', dict(status='shape gate failed for both arms; Part C not run',
                                          gates={a: shapes['arms'][a]['gate'] for a in arms}))
        return
    model = models[arm][shapes['arms'][arm]['selected']]
    save(output/'shape_model.json', model.description())
    evidence = part_c(output, arm, model, r2_lines, targets, hands)
    evidence['gates'] = {a: shapes['arms'][a]['gate'] for a in arms}
    save(output/'evidence.json', evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/word_shapes_2026-10-09')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
