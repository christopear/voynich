"""Preregistered frequency-ranked codeword assignment on the stage-31 shape model (stage 32)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e28_word_homophones import save
from voynich.experiments import e31_word_shapes as e31
from voynich.laboratory.codebook_assignment import page_encrypt, ranked_codebook
from voynich.laboratory.forward_screen import broad_model, run_screen, source_frequencies, vocabulary
from voynich.laboratory.manifest import environment
from voynich.laboratory.structured_codes import RULES, serialized_bits
from voynich.laboratory.word_shapes import page_hands
from voynich.paths import ROOT

STAGE31 = ROOT/'results/word_shapes_2026-10-09'
PROTOCOL = ROOT/'docs/protocols/RANKED_ASSIGNMENT_2026-10-09.md'


def setup():
    slots = json.loads(e31.STAGE29.read_text())
    targets = {name: slots[name] for name in e31.TARGETS}
    _, lines, arms = e31.training_arms(targets)
    model = broad_model(arms)
    stored = json.loads((STAGE31/'shape_model.json').read_text())
    assert json.loads(json.dumps(model.description())) == stored, 'shape model differs from stage 31'
    return targets, lines, model


def paired(records, stage31):
    """Per-key differences from stage 31 (same strings, random assignment)."""
    old = {(r['split'], r['setting'], r['seed'], r['passage']): r for r in stage31 if r['family'] == 'cipher'}
    out = []
    for r in records:
        if r['family'] != 'cipher':
            continue
        o = old[(r['split'], r['setting'], r['seed'], r['passage'])]
        out.append(dict(split=r['split'], rule=r['rule'], seed=r['seed'], passage=r['passage'],
                        mean_length=r['profile']['vector'][5]-o['profile']['vector'][5],
                        glyph_h=r['profile']['vector'][6]-o['profile']['vector'][6],
                        section_excess=r['profile']['vector'][2]-o['profile']['vector'][2]))
    summary = {k: dict(median=float(np.median([p[k] for p in out])), min=float(min(p[k] for p in out)),
                       max=float(max(p[k] for p in out))) for k in ('mean_length', 'glyph_h', 'section_excess')}
    return dict(summary=summary, pairs=out)


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT/'src/voynich/laboratory/codebook_assignment.py',
             ROOT/'src/voynich/laboratory/forward_screen.py', ROOT/'src/voynich/laboratory/word_shapes.py',
             ROOT/'src/voynich/experiments/e31_word_shapes.py', ROOT/'src/voynich/laboratory/structured_codes.py',
             ROOT/'src/voynich/mechanism_models.py', e31.ZL, e31.STAGE29, e31.STAGE28, e31.PREPARED,
             STAGE31/'shape_model.json', STAGE31/'generated.json', PROTOCOL]
    save(output/'manifest.json', dict(environment=environment(ROOT),
                                      hashes={str(p.relative_to(ROOT)): sha(p) for p in paths}))
    targets, lines, model = setup()
    hands = page_hands(e31.ZL)
    vocab, freqs = vocabulary(), source_frequencies()
    make = lambda seed: ranked_codebook(vocab, freqs, model, seed)[0]
    books = {}
    costs = {}
    for seed in range(101, 107):
        books[seed], draws = ranked_codebook(vocab, freqs, model, seed)
        costs[seed] = dict(books[seed].costs(), model_draws=draws)
    save(output/'codebooks.json', {seed: book.encode for seed, book in books.items()})
    save(output/'costs.json', dict(cipher=costs, shape_model_serialization_bits=serialized_bits(model.description()),
                                   plaintext_frequency_table_bits=serialized_bits(dict(sorted(freqs.items()))),
                                   note='Explicit serialization/reference budgets; no MDL ranking.'))
    evidence = run_screen(output, books=books, make_book=make, rules=RULES, encrypt=page_encrypt,
                          r2_lines=lines, targets=targets, hands=hands)
    records = json.loads((output/'generated.json').read_text())
    stage31 = json.loads((STAGE31/'generated.json').read_text())
    evidence['paired_with_stage31'] = paired(records, stage31)
    save(output/'evidence.json', evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/ranked_assignment_2026-10-09')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
