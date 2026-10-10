"""Check stage-29 decomposition totals with the independent scalar estimator."""
import argparse
import json
import math
from pathlib import Path

from voynich.experiments.e27_unit_association import association, sha
from voynich.experiments.e28_word_homophones import save
from voynich.paths import ROOT


def verify(folder):
    evidence = json.loads((folder/'evidence.json').read_text())
    slots = json.loads((folder/'slots.json').read_text())
    checked = 0

    def compare(tokens, rows, stored):
        nonlocal checked
        for condition in ('section', 'roles'):
            scalar = association(tokens, rows, condition, seed=2901)
            for key in ('raw', 'null_mean', 'excess', 'null_sd', 'null_mean_mcse'):
                assert math.isclose(stored[condition]['total'][key], scalar[key], abs_tol=1e-10)
            for key in ('raw', 'null_mean', 'excess'):
                assert math.isclose(sum(b[key] for b in stored[condition]['bins'].values()),
                                    scalar[key], abs_tol=1e-10)
            checked += 1

    for name, rows in slots.items():
        assert len(rows) in (512, 1024)
        assert len({r['folio'] for r in rows}) == len(rows)//64
        compare([r['word'] for r in rows], rows, evidence['manuscript'][name])
    for currier in ('A', 'B'):
        early = {r['folio'] for r in slots[currier+'_ZL_split_early']}
        late = {r['folio'] for r in slots[currier+'_ZL_split_late']}
        assert early.isdisjoint(late)
    previous = ROOT/'results/word_homophones_2026-10-09'
    sources = json.loads((previous/'source_panels.json').read_text())
    for source, panels in sources.items():
        for panel in panels:
            name = f"{source}_{panel['split']}_{panel['seed']}"
            layout = 'previous_ZL_original' if panel['split'] == 'development' else 'previous_ZL_additional'
            compare(panel['words'], slots[layout], evidence['reference'][name])
    for path, digest in json.loads((folder/'manifest.json').read_text())['hashes'].items():
        assert sha(ROOT/path) == digest, path
    result = dict(scalar_comparisons=checked, all_agree_at_tolerance=1e-10,
                  folio_disjointness=True, manifest_hashes=True)
    save(folder/'verification.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'results/frequency_currier_a_2026-10-09')
    print(verify(parser.parse_args().directory))


if __name__ == '__main__':
    main()
