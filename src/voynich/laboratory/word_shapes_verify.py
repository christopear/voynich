"""Replay stage 31: hashes, scribe tables, shape models and gate, codebooks and every generated panel."""
import argparse
import json
from pathlib import Path

import numpy as np

from voynich import mechanism_models as mm
from voynich.experiments.e27_unit_association import sha
from voynich.experiments import e31_word_shapes as e31
from voynich.laboratory.structured_codes import WordCodebook
from voynich.laboratory.word_shapes import NGramModel, model_codebook, page_hands, scribe_measure
from voynich.paths import ROOT


def close(a, b):
    return json.loads(json.dumps(a)) == json.loads(json.dumps(b))


def verify(folder):
    read = lambda name: json.loads((folder/name).read_text())
    for path, digest in read('manifest.json')['hashes'].items():
        assert sha(ROOT/path) == digest, path
    hands = page_hands(e31.ZL)
    assert close(hands, read('hands.json'))
    slots = json.loads(e31.STAGE29.read_text())
    scribe = read('scribe.json')
    assert scribe['calibration']['passed']
    for name, rows in slots.items():
        measured = scribe_measure([r['word'] for r in rows], rows, hands)
        assert close(measured, scribe['manuscript'][name]), name
        if set(measured['hands']) == {'1'}:
            assert measured['section'] == measured['section_hand'], name
    targets = read('slots.json')
    assert all(close(targets[n], slots[n]) for n in e31.TARGETS)
    dev, val = targets['B_ZL_split_early'], targets['B_ZL_split_late']
    assert {r['folio'] for r in dev}.isdisjoint(r['folio'] for r in val)
    training = read('training.json')
    assert set(training['broad_folios']).isdisjoint(training['reserved_folios'])
    reserved, lines, arms = e31.training_arms(targets)
    assert sorted(reserved) == training['reserved_folios'] and sorted(arms['broad']) == training['broad_folios']
    broad = [w for ws in arms['broad'].values() for w in ws]
    assert len(broad) == training['broad_tokens']
    shapes = read('shapes.json')
    assert close(e31.part_b(arms, targets)[0], shapes)
    evidence = read('evidence.json')
    if 'arm' not in evidence:
        assert not any(shapes['arms'][a]['gate']['passed'] for a in shapes['arms'])
        return dict(part_c=False)
    arm = evidence['arm']
    assert arm == ('broad' if shapes['arms']['broad']['gate']['passed'] else 'matched')
    words = broad if arm == 'broad' else [r['word'] for r in dev]
    order = int(shapes['arms'][arm]['selected'][1:])
    model = NGramModel(words, order)
    assert close(model.description(), read('shape_model.json'))
    vocabulary = sorted({w for ch in json.loads(e31.PREPARED.read_text())['cucina'] for w in ch['words']})
    books = {int(seed): WordCodebook(mapping) for seed, mapping in read('codebooks.json').items()}
    for seed, book in books.items():
        assert model_codebook(vocabulary, model, seed)[0].encode == book.encode
    panels = {p['seed']: p for p in read('source_panels.json')}
    dev_chapters = {s['chapter'] for p in panels.values() if p['split'] == 'development' for s in p['spans']}
    val_chapters = {s['chapter'] for p in panels.values() if p['split'] == 'validation' for s in p['spans']}
    assert dev_chapters.isdisjoint(val_chapters)
    train = mm.Training(lines if arm == 'broad' else e31.training_lines(dev))
    records = read('generated.json')
    assert len(records) == 168
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
            tokens, audit = mm.generate(train, None, '', 512, record['config'], record['seed'])
        assert tokens == record['tokens'] and close(audit, record['audit'])
        assert close(e31.profile(tokens, rows), record['profile'])
    calibration = read('calibration.json')
    assert calibration['passed'] == sum(c['selected']['distance'] <= 2 for c in calibration['records'])
    development = [r for r in records if r['split'] == 'development']
    candidates = e31.medians(development, 'cipher')
    for c in calibration['records']:
        assert close(e31.closest(c['profile']['vector'], candidates), c['selected'])
    assert close(e31.discrimination(development), calibration['discrimination'])
    target = evidence['targets']['B_ZL_split_early']['profile']['vector']
    for family, chosen in evidence['selection'].items():
        assert close(e31.closest(target, e31.medians(development, family)), chosen)
        for name, comparison in evidence['comparisons'][family].items():
            observed = np.array(evidence['targets'][name]['profile']['vector'])
            for draw in comparison['draws']:
                assert abs(e31.distance(draw['profile']['vector'], observed) - draw['distance']) < 1e-12
            assert comparison['hits'] == sum(d['distance'] <= 1 for d in comparison['draws'])
    return dict(part_c=True, panels=len(records), cipher_tokens_roundtripped=roundtrips,
                calibration=len(calibration['records']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'results/word_shapes_2026-10-09')
    result = verify(parser.parse_args().directory)
    print(json.dumps(result))
    (parser.parse_args().directory/'verification.json').write_text(json.dumps(dict(result, passed=True))+'\n')


if __name__ == '__main__':
    main()
