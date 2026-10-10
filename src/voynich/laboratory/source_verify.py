"""Replay stage 34 (source sensitivity) for every source and re-derive every reported number."""
import argparse
import json
from pathlib import Path

from voynich import mechanism_models as mm
from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e31_word_shapes import profile
from voynich.experiments.e34_source_sensitivity import (
    SOURCES, STAGE33, all_rule_hits, books_for, common, plaintext_association,
)
from voynich.experiments import e31_word_shapes as e31
from voynich.laboratory.context_choice import CONTEXT_RULES
from voynich.laboratory.forward_screen import calibrate, compare, frequency_length
from voynich.laboratory.forward_verify import same
from voynich.laboratory.word_shapes import page_hands
from voynich.paths import ROOT


def verify(folder):
    read = lambda name: json.loads((folder/name).read_text())
    for path, digest in read('manifest.json')['hashes'].items():
        assert sha(ROOT/path) == digest, path
    targets, lines, model, encrypt = common()
    hands = page_hands(e31.ZL)
    dev, val = targets['B_ZL_split_early'], targets['B_ZL_split_late']
    train = mm.Training(lines)
    evidence = read('evidence.json')['sources']
    stage33 = {(r['family'], r['split'], r['setting'], r['seed'], r.get('passage')): r['tokens']
               for r in json.loads((STAGE33/'generated.json').read_text())}
    summary = {}
    for source in SOURCES:
        books, make, panels = books_for(source, model)
        assert {str(s): b.encode for s, b in books.items()} == read(f'codebooks_{source}.json')
        assert same(panels, read(f'source_panels_{source}.json'))
        by_seed = {p['seed']: p for p in panels}
        records = read(f'generated_{source}.json')
        roundtrips = 0
        for r in records:
            rows = dev if r['split'] == 'development' else val
            if r['family'] == 'cipher':
                panel, book = by_seed[r['passage']], books[r['seed']]
                tokens, audit = encrypt(book, panel['words'], rows, r['rule'], 10000+100*panel['seed']+r['seed'])
                assert book.decrypt(tokens) == panel['words']
                roundtrips += len(tokens)
            else:
                tokens, audit = mm.generate(train, None, '', 512, r['config'], r['seed'])
            assert tokens == r['tokens'] and same(audit, r['audit'])
            assert same(profile(tokens, rows), r['profile']) and same(frequency_length(tokens), r['frequency_length'])
            if source == 'cucina' or r['family'] == 'R2':
                assert stage33[(r['family'], r['split'], r['setting'], r['seed'], r.get('passage'))] == tokens
        development = [r for r in records if r['split'] == 'development']
        calibration = calibrate(make, CONTEXT_RULES, encrypt, panels, dev, development)
        assert same(calibration, read(f'calibration_{source}.json'))
        result = evidence[source]
        assert result['calibration_passed'] == calibration['passed']
        assert same(plaintext_association(panels, targets), result['plaintext_association'])
        if calibration['passed'] >= 12:
            recomputed = compare(records, targets, hands)
            for key, value in recomputed.items():
                assert same(value, result[key]), (source, key)
            assert same(all_rule_hits(records, result['targets'], targets), result['all_rule_hits'])
        summary[source] = dict(panels=len(records), cipher_tokens_roundtripped=roundtrips)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'results/source_sensitivity_2026-10-09')
    folder = parser.parse_args().directory
    result = verify(folder)
    print(json.dumps(result))
    (folder/'verification.json').write_text(json.dumps(dict(result, passed=True))+'\n')


if __name__ == '__main__':
    main()
