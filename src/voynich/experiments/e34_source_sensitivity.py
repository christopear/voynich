"""Preregistered plaintext source sensitivity under the frozen stage-33 mechanism (stage 34)."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from voynich import mechanism_models as mm
from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e28_word_homophones import save
from voynich.experiments import e31_word_shapes as e31
from voynich.experiments.e29_frequency_currier_a import decomposition
from voynich.experiments.e32_ranked_assignment import setup
from voynich.laboratory.codebook_assignment import ranked_codebook
from voynich.laboratory.context_choice import CONTEXT_RULES, make_encrypt
from voynich.laboratory.forward_screen import calibrate, compare, generate
from voynich.laboratory.manifest import environment
from voynich.laboratory.word_shapes import page_hands
from voynich.paths import ROOT

SOURCES = ('celsus', 'pliny', 'cucina')
STAGE33 = ROOT/'results/context_choice_2026-10-09'
PROTOCOL = ROOT/'docs/protocols/SOURCE_SENSITIVITY_2026-10-09.md'


def source_data(source):
    prepared = json.loads(e31.PREPARED.read_text())[source]
    frequencies = Counter(w for ch in prepared for w in ch['words'])
    panels = [dict(p, words=p['words'][:512], spans=p['spans'][:8])
              for p in json.loads(e31.STAGE28.read_text())[source]]
    return sorted(frequencies), frequencies, panels


def common():
    targets, lines, model = setup()
    lift = mm.Training(lines).edge
    return targets, lines, model, make_encrypt(lift)


def books_for(source, model):
    vocabulary, frequencies, panels = source_data(source)
    make = lambda seed: ranked_codebook(vocabulary, frequencies, model, seed)[0]
    return {seed: make(seed) for seed in range(101, 107)}, make, panels


def plaintext_association(panels, targets):
    out = {}
    for panel in panels:
        rows = targets['B_ZL_split_early'] if panel['split'] == 'development' else targets['B_ZL_split_late']
        out[str(panel['seed'])] = dict(split=panel['split'],
            section=decomposition(panel['words'], rows)['total']['excess'],
            roles=decomposition(panel['words'], rows, 'roles')['total']['excess'])
    return out


def all_rule_hits(records, measured, targets):
    """Descriptive hits for every rule and target; unselected rules carry no claim."""
    out = {}
    for setting, rule in enumerate(CONTEXT_RULES):
        out[rule] = {}
        for name, observed in measured.items():
            split = 'development' if name.endswith('early') else 'validation'
            draws = [r for r in records if r['family'] == 'cipher' and r['setting'] == setting and r['split'] == split]
            distances = []
            for r in draws:
                prof = r['profile'] if name in ('B_ZL_split_early', 'B_ZL_split_late') else e31.profile(r['tokens'], targets[name])
                distances.append(e31.distance(prof['vector'], observed['profile']['vector']))
            out[rule][name] = dict(hits=sum(d <= 1 for d in distances), total=len(distances), best=min(distances))
    return out


def screen(source, model, encrypt, lines, targets, hands):
    books, make, panels = books_for(source, model)
    dev, val = targets['B_ZL_split_early'], targets['B_ZL_split_late']
    records = generate(books, CONTEXT_RULES, encrypt, panels, mm.Training(lines), dev, val)
    development = [r for r in records if r['split'] == 'development']
    calibration = calibrate(make, CONTEXT_RULES, encrypt, panels, dev, development)
    result = dict(source=source, vocabulary=len(books[101].encode), calibration_passed=calibration['passed'],
                  balanced_accuracy=calibration['discrimination']['balanced_accuracy'],
                  plaintext_association=plaintext_association(panels, targets))
    if calibration['passed'] >= 12:
        result.update(compare(records, targets, hands))
        result['all_rule_hits'] = all_rule_hits(records, result['targets'], targets)
    else:
        result['status'] = 'calibration failed; manuscript comparison stopped'
    return books, panels, records, calibration, result


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT/'src/voynich/laboratory/context_choice.py',
             ROOT/'src/voynich/laboratory/codebook_assignment.py', ROOT/'src/voynich/laboratory/forward_screen.py',
             ROOT/'src/voynich/laboratory/word_shapes.py', ROOT/'src/voynich/experiments/e31_word_shapes.py',
             ROOT/'src/voynich/experiments/e32_ranked_assignment.py', ROOT/'src/voynich/experiments/e29_frequency_currier_a.py',
             ROOT/'src/voynich/laboratory/structured_codes.py', ROOT/'src/voynich/mechanism_models.py',
             e31.ZL, e31.STAGE29, e31.STAGE28, e31.PREPARED, STAGE33/'generated.json', PROTOCOL]
    save(output/'manifest.json', dict(environment=environment(ROOT),
                                      hashes={str(p.relative_to(ROOT)): sha(p) for p in paths}))
    targets, lines, model, encrypt = common()
    hands = page_hands(e31.ZL)
    evidence = {}
    for source in SOURCES:
        books, panels, records, calibration, result = screen(source, model, encrypt, lines, targets, hands)
        save(output/f'codebooks_{source}.json', {seed: b.encode for seed, b in books.items()})
        save(output/f'source_panels_{source}.json', panels)
        save(output/f'generated_{source}.json', records)
        save(output/f'calibration_{source}.json', calibration)
        evidence[source] = result
        print(source, 'done', flush=True)
    save(output/'evidence.json', dict(status='descriptive forward-model screen; no key recovery or readings',
                                      sources=evidence))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/source_sensitivity_2026-10-09')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
