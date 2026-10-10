"""Replay the stage 31-34 corrective rerun and re-derive every reported number."""
import argparse
import json
from pathlib import Path

from voynich import mechanism_models as mm
from voynich.experiments.e27_unit_association import sha
from voynich.experiments import e31_word_shapes as e31
from voynich.experiments import posthoc_e31_boundary_correction as bc
from voynich.experiments.e30_structured_word_codes import R2
from voynich.experiments.e32_ranked_assignment import setup
from voynich.laboratory.boundary_correction import CONTEXT_RULES, make_context_encrypt, page_encrypt, profile
from voynich.laboratory.forward_screen import frequency_length
from voynich.laboratory.forward_verify import same
from voynich.laboratory.structured_codes import RULES
from voynich.laboratory.word_shapes import page_hands
from voynich.paths import ROOT


def verify(folder):
    read = lambda name: json.loads((folder/name).read_text())
    for path, digest in read('manifest.json')['hashes'].items():
        assert sha(ROOT/path) == digest, path
    hands = page_hands(e31.ZL)
    targets = bc.annotated_targets()
    assert same(targets, read('slots.json'))
    _, lines, model = setup()
    _, _, arms = e31.training_arms(json.loads(e31.STAGE29.read_text()))
    assert same(bc.scribe_direct(hands, json.loads(e31.STAGE28.read_text())), read('scribe.json'))
    assert same(bc.enumeration_check(arms, targets), read('enumeration.json'))
    train = mm.Training(lines)
    context = make_context_encrypt(train.edge)
    streams = {(s['split'], s['setting'], s['seed']): s for s in read('r2_streams.json')}
    for (split, setting, seed), stream in streams.items():
        tokens, audit = mm.generate(train, None, '', 512, R2[setting], seed)
        assert tokens == stream['tokens'] and same(audit, stream['audit'])
    evidence = read('evidence.json')['grids']
    summary = {}
    for name, source, assignment, kind in bc.GRIDS:
        books, make, panels = bc.grid_books(source, assignment, model)
        assert {str(s): b.encode for s, b in books.items()} == json.loads(bc.STORED[name].read_text()), name
        rules, encrypt = (RULES, page_encrypt) if kind == 'page' else (CONTEXT_RULES, context)
        by_seed = {p['seed']: p for p in panels}
        records = read(f'generated_{name}.json')
        roundtrips = 0
        for r in records:
            rows = targets[r['layout']]
            if r['family'] == 'cipher':
                panel, book = by_seed[r['passage']], books[r['seed']]
                tokens, audit = encrypt(book, panel['words'], rows, r['rule'], 10000+100*panel['seed']+r['seed'])
                assert book.decrypt(tokens) == panel['words']
                assert tokens == r['tokens'] and same(audit, r['audit'])
                roundtrips += len(tokens)
            else:
                tokens = streams[(r['split'], r['setting'], r['seed'])]['tokens']
            assert same(profile(tokens, rows), r['profile']), (name, r['layout'])
            assert same(frequency_length(tokens), r['frequency_length'])
        stripped = [{k: v for k, v in r.items() if k != 'distance'} for r in records]
        development = [r for r in stripped if r['split'] == 'development']
        calibration = bc.calibrate(make, rules, encrypt, panels, targets['B_ZL_split_early'], development)
        discrimination = e31.discrimination(development)
        calibration['discrimination'] = dict(by_family=discrimination['by_family'],
                                             balanced_accuracy=discrimination['balanced_accuracy'])
        assert same(calibration, read(f'calibration_{name}.json'))
        result = evidence[name]
        assert result['calibration_passed'] == calibration['passed']
        if calibration['passed'] >= 12:
            for key, value in bc.compare(stripped, targets, hands).items():
                assert same(value, result[key]), (name, key)
            assert same([r['distance'] for r in stripped], [r['distance'] for r in records])
        summary[name] = dict(records=len(records), cipher_tokens_roundtripped=roundtrips)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'results/boundary_correction_2026-10-10')
    folder = parser.parse_args().directory
    result = verify(folder)
    print(json.dumps(result))
    (folder/'verification.json').write_text(json.dumps(dict(result, passed=True))+'\n')


if __name__ == '__main__':
    main()
