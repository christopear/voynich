"""Preregistered context-conditioned variant choice on stage-32 ranked codebooks (stage 33)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from voynich import mechanism_models as mm
from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e28_word_homophones import save
from voynich.experiments import e31_word_shapes as e31
from voynich.experiments.e32_ranked_assignment import STAGE31, setup
from voynich.laboratory.codebook_assignment import ranked_codebook
from voynich.laboratory.context_choice import CONTEXT_RULES, make_encrypt
from voynich.laboratory.forward_screen import run_screen, source_frequencies, vocabulary
from voynich.laboratory.manifest import environment
from voynich.laboratory.structured_codes import serialized_bits
from voynich.laboratory.word_shapes import page_hands
from voynich.paths import ROOT

STAGE32 = ROOT/'results/ranked_assignment_2026-10-09'
PROTOCOL = ROOT/'docs/protocols/CONTEXT_CHOICE_2026-10-09.md'
MEASURES = {'coupling': 7, 'mean_length': 5, 'glyph_h': 6, 'section_excess': 2}


def books_and_encrypt():
    targets, lines, model = setup()
    vocab, freqs = vocabulary(), source_frequencies()
    make = lambda seed: ranked_codebook(vocab, freqs, model, seed)[0]
    books = {seed: make(seed) for seed in range(101, 107)}
    stored = json.loads((STAGE32/'codebooks.json').read_text())
    assert {str(s): b.encode for s, b in books.items()} == stored, 'codebooks differ from stage 32'
    lift = mm.Training(lines).edge
    return targets, lines, books, make, lift, make_encrypt(lift)


def paired(records, stage32):
    """Per-key differences from stage-32 IID (setting 0), matched by split, key and passage."""
    base = {(r['split'], r['seed'], r['passage']): r for r in stage32 if r['family'] == 'cipher' and r['setting'] == 0}
    out = {}
    for rule in CONTEXT_RULES:
        diffs = []
        for r in records:
            if r['family'] != 'cipher' or r['rule'] != rule:
                continue
            b = base[(r['split'], r['seed'], r['passage'])]
            diffs.append({k: r['profile']['vector'][i]-b['profile']['vector'][i] for k, i in MEASURES.items()})
        out[rule] = {k: dict(median=float(np.median([d[k] for d in diffs])), min=float(min(d[k] for d in diffs)),
                             max=float(max(d[k] for d in diffs))) for k in MEASURES}
    return out


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT/'src/voynich/laboratory/context_choice.py',
             ROOT/'src/voynich/laboratory/codebook_assignment.py', ROOT/'src/voynich/laboratory/forward_screen.py',
             ROOT/'src/voynich/laboratory/word_shapes.py', ROOT/'src/voynich/experiments/e31_word_shapes.py',
             ROOT/'src/voynich/experiments/e32_ranked_assignment.py',
             ROOT/'src/voynich/laboratory/structured_codes.py', ROOT/'src/voynich/mechanism_models.py',
             e31.ZL, e31.STAGE29, e31.STAGE28, e31.PREPARED, STAGE31/'shape_model.json',
             STAGE32/'codebooks.json', STAGE32/'generated.json', PROTOCOL]
    save(output/'manifest.json', dict(environment=environment(ROOT),
                                      hashes={str(p.relative_to(ROOT)): sha(p) for p in paths}))
    targets, lines, books, make, lift, encrypt = books_and_encrypt()
    hands = page_hands(e31.ZL)
    save(output/'codebooks.json', {seed: book.encode for seed, book in books.items()})
    table = {f'{a} {b}': v for (a, b), v in sorted(lift.items())}
    save(output/'lift.json', table)
    save(output/'costs.json', dict(lift_table_serialization_bits=serialized_bits(table),
                                   note='Lift table is the existing R2 edge table from the same training lines.'))
    evidence = run_screen(output, books=books, make_book=make, rules=CONTEXT_RULES, encrypt=encrypt,
                          r2_lines=lines, targets=targets, hands=hands)
    records = json.loads((output/'generated.json').read_text())
    stage32 = json.loads((STAGE32/'generated.json').read_text())
    evidence['paired_with_stage32_iid'] = paired(records, stage32)
    save(output/'evidence.json', evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/context_choice_2026-10-09')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
