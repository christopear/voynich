"""Replay a forward screen produced by voynich.laboratory.forward_screen (stages 32 onward)."""
from __future__ import annotations

import json

from voynich import mechanism_models as mm
from voynich.experiments.e27_unit_association import sha
from voynich.laboratory.forward_screen import calibrate, compare, frequency_length, passages
from voynich.experiments.e31_word_shapes import profile
from voynich.paths import ROOT


def same(a, b):
    return json.loads(json.dumps(a)) == json.loads(json.dumps(b))


def verify_screen(folder, *, books, make_book, rules, encrypt, r2_lines, targets, hands):
    read = lambda name: json.loads((folder/name).read_text())
    for path, digest in read('manifest.json')['hashes'].items():
        assert sha(ROOT/path) == digest, path
    stored = {int(k): v for k, v in read('codebooks.json').items()}
    assert {s: b.encode for s, b in books.items()} == stored
    panels = passages()
    assert same(panels, read('source_panels.json'))
    dev_ch = {s['chapter'] for p in panels if p['split'] == 'development' for s in p['spans']}
    val_ch = {s['chapter'] for p in panels if p['split'] == 'validation' for s in p['spans']}
    assert dev_ch.isdisjoint(val_ch)
    dev, val = targets['B_ZL_split_early'], targets['B_ZL_split_late']
    assert {r['folio'] for r in dev}.isdisjoint(r['folio'] for r in val)
    by_seed = {p['seed']: p for p in panels}
    train = mm.Training(r2_lines)
    records = read('generated.json')
    roundtrips = 0
    for record in records:
        rows = dev if record['split'] == 'development' else val
        if record['family'] == 'cipher':
            panel = by_seed[record['passage']]
            book = books[record['seed']]
            tokens, audit = encrypt(book, panel['words'], rows, record['rule'],
                                    10000+100*panel['seed']+record['seed'])
            assert book.decrypt(tokens) == panel['words']
            roundtrips += len(tokens)
        else:
            tokens, audit = mm.generate(train, None, '', 512, record['config'], record['seed'])
        assert tokens == record['tokens'] and same(audit, record['audit'])
        assert same(profile(tokens, rows), record['profile'])
        assert same(frequency_length(tokens), record['frequency_length'])
    development = [r for r in records if r['split'] == 'development']
    calibration = calibrate(make_book, rules, encrypt, panels, dev, development)
    assert same(calibration, read('calibration.json'))
    evidence = read('evidence.json')
    if calibration['passed'] >= 12:
        recomputed = compare(records, targets, hands)
        for key, value in recomputed.items():
            assert same(value, evidence[key]), key
    return dict(panels=len(records), cipher_tokens_roundtripped=roundtrips,
                calibration=calibration['passed'], evidence=evidence)
