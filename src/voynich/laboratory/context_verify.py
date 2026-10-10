"""Replay stage 33 (context-conditioned choice) and re-derive every reported number."""
import argparse
import json
from pathlib import Path

from voynich.experiments import e31_word_shapes as e31
from voynich.experiments.e33_context_choice import STAGE32, books_and_encrypt, paired
from voynich.laboratory.context_choice import CONTEXT_RULES
from voynich.laboratory.forward_verify import same, verify_screen
from voynich.laboratory.word_shapes import page_hands
from voynich.paths import ROOT


def verify(folder):
    targets, lines, books, make, lift, encrypt = books_and_encrypt()
    assert same({f'{a} {b}': v for (a, b), v in sorted(lift.items())}, json.loads((folder/'lift.json').read_text()))
    result = verify_screen(folder, books=books, make_book=make, rules=CONTEXT_RULES, encrypt=encrypt,
                           r2_lines=lines, targets=targets, hands=page_hands(e31.ZL))
    records = json.loads((folder/'generated.json').read_text())
    stage32 = json.loads((STAGE32/'generated.json').read_text())
    assert same(paired(records, stage32), result.pop('evidence')['paired_with_stage32_iid'])
    old = {(r['family'], r['split'], r['setting'], r['seed'], r.get('passage')): r['tokens'] for r in stage32}
    for r in records:
        if r['family'] == 'R2' or r['rule'] == 'iid':
            assert old[(r['family'], r['split'], r['setting'], r['seed'], r.get('passage'))] == r['tokens']
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'results/context_choice_2026-10-09')
    folder = parser.parse_args().directory
    result = verify(folder)
    print(json.dumps(result))
    (folder/'verification.json').write_text(json.dumps(dict(result, passed=True))+'\n')


if __name__ == '__main__':
    main()
