"""Replay stage 32 (frequency-ranked assignment) and re-derive every reported number."""
import argparse
import json
from pathlib import Path

from voynich.experiments import e31_word_shapes as e31
from voynich.experiments.e32_ranked_assignment import STAGE31, paired, setup
from voynich.laboratory.codebook_assignment import page_encrypt, ranked_codebook
from voynich.laboratory.forward_screen import source_frequencies, vocabulary
from voynich.laboratory.forward_verify import same, verify_screen
from voynich.laboratory.structured_codes import RULES
from voynich.laboratory.word_shapes import model_codebook, page_hands
from voynich.paths import ROOT


def verify(folder):
    targets, lines, model = setup()
    vocab, freqs = vocabulary(), source_frequencies()
    books = {s: ranked_codebook(vocab, freqs, model, s)[0] for s in range(101, 107)}
    for seed, book in books.items():
        base = model_codebook(vocab, model, seed)[0]
        assert sorted(c for cs in base.encode.values() for c in cs) == sorted(c for cs in book.encode.values() for c in cs)
    result = verify_screen(folder, books=books, make_book=lambda s: ranked_codebook(vocab, freqs, model, s)[0],
                           rules=RULES, encrypt=page_encrypt, r2_lines=lines, targets=targets,
                           hands=page_hands(e31.ZL))
    records = json.loads((folder/'generated.json').read_text())
    stage31 = json.loads((STAGE31/'generated.json').read_text())
    assert same(paired(records, stage31), result.pop('evidence')['paired_with_stage31'])
    old = {(r['family'], r['split'], r['setting'], r['seed']): r['tokens'] for r in stage31 if r['family'] == 'R2'}
    assert all(old[(r['family'], r['split'], r['setting'], r['seed'])] == r['tokens'] for r in records if r['family'] == 'R2')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'results/ranked_assignment_2026-10-09')
    folder = parser.parse_args().directory
    result = verify(folder)
    print(json.dumps(result))
    (folder/'verification.json').write_text(json.dumps(dict(result, passed=True))+'\n')


if __name__ == '__main__':
    main()
