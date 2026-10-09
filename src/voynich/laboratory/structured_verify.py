"""Replay stage 30's fixed dictionaries, random choices, R2 and stored profiles."""
import argparse
import json
from pathlib import Path

import numpy as np

from voynich import mechanism_models as mm
from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e28_word_homophones import save
from voynich.experiments.e30_structured_word_codes import profile, training_lines, distance, closest, medians
from voynich.laboratory.structured_codes import SlotGrammar, WordCodebook, order_diagnostic
from voynich.paths import ROOT


def verify(folder):
    read = lambda name: json.loads((folder/name).read_text())
    for path, digest in read('manifest.json')['hashes'].items():
        assert sha(ROOT/path) == digest, path
    slots = read('slots.json')
    dev, val = slots['B_ZL_split_early'], slots['B_ZL_split_late']
    assert {r['folio'] for r in dev}.isdisjoint(r['folio'] for r in val)
    panels = {p['seed']: p for p in read('source_panels.json')}
    dev_chapters = {s['chapter'] for p in panels.values() if p['split'] == 'development' for s in p['spans']}
    val_chapters = {s['chapter'] for p in panels.values() if p['split'] == 'validation' for s in p['spans']}
    assert dev_chapters.isdisjoint(val_chapters)
    grammar = SlotGrammar.fit([r['word'] for r in dev])
    description = read('grammar.json')
    for k, value in grammar.description().items():
        assert json.loads(json.dumps(value)) == description[k], k
    books = {int(seed): WordCodebook(mapping) for seed, mapping in read('codebooks.json').items()}
    for seed, book in books.items():
        assert WordCodebook.make(book.encode, grammar, seed).encode == book.encode
        assert set(c for cs in book.encode.values() for c in cs) <= set(grammar.weights)
    records = read('generated.json')
    assert len(records) == 168
    training = mm.Training(training_lines(dev))
    roundtrips = 0
    for record in records:
        rows = dev if record['split'] == 'development' else val
        if record['family'] == 'cipher':
            book = books[record['seed']]
            panel = panels[record['passage']]
            tokens, audit = book.encrypt(panel['words'], [r['page'] for r in rows], record['rule'],
                                        10000+100*panel['seed']+record['seed'])
            assert book.decrypt(tokens) == panel['words']
            roundtrips += len(tokens)
        else:
            tokens, audit = mm.generate(training, None, '', 512, record['config'], record['seed'])
        assert tokens == record['tokens'] and audit == record['audit']
        assert profile(tokens, rows) == record['profile']
        assert order_diagnostic(tokens, rows) == record['order']
    calibration = read('calibration.json')
    candidates = medians([r for r in records if r['split'] == 'development'], 'cipher')
    for c in calibration['records']:
        book = WordCodebook.make(next(iter(books.values())).encode, grammar, c['key_seed'])
        tokens, _ = book.encrypt(panels[c['passage']]['words'], [r['page'] for r in dev], c['rule'],
                                10000+100*c['passage']+c['key_seed'])
        measured = profile(tokens, dev)
        assert measured == c['profile']
        assert closest(measured['vector'], candidates) == c['selected']
    evidence = read('evidence.json')
    comparisons = 0
    for name, target in evidence.get('targets', {}).items():
        rows = slots[name]
        assert profile([r['word'] for r in rows], rows) == target['profile']
        assert order_diagnostic([r['word'] for r in rows], rows) == target['order']
    for family, targets in evidence.get('comparisons', {}).items():
        for name, group in targets.items():
            target = evidence['targets'][name]['profile']['vector']
            for draw in group['draws']:
                split = 'development' if name.endswith('early') else 'validation'
                record = next(r for r in records if r['family'] == family and r['split'] == split
                              and r['setting'] == evidence['selection'][family]['setting']
                              and r['seed'] == draw['seed'] and r.get('passage') == draw['passage'])
                measured = profile(record['tokens'], slots[name])
                assert measured == draw['profile']
                assert distance(measured['vector'], target) == draw['distance']
                assert (np.array(measured['vector'])-target).tolist() == draw['signed_residual']
                comparisons += 1
            assert group['hits'] == sum(d['distance'] <= 1 for d in group['draws'])
    result = dict(replayed_panels=len(records), known_key_word_roundtrips=roundtrips,
                  calibration_replays=len(calibration['records']), comparison_recomputations=comparisons,
                  manifest_hashes=True, chapter_and_folio_disjointness=True)
    save(folder/'verification.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'results/structured_word_codes_2026-10-09')
    print(verify(parser.parse_args().directory))


if __name__ == '__main__':
    main()
