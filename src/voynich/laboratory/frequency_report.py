"""Render the stored stage-29 evidence without rerunning the study."""
import argparse
import json
from pathlib import Path

from voynich.laboratory.unit_association_report import Report
from voynich.paths import ROOT


def render(folder):
    evidence = json.loads((folder/'evidence.json').read_text())
    calibration = json.loads((folder/'calibration.json').read_text())
    slots = json.loads((folder/'slots.json').read_text())
    manuscript = evidence['manuscript']
    report = Report('Voynich: which words carry the page signal?')
    report.p('Stage 29, 9 October 2026. Evidence label: descriptive structural diagnostic. '
             'No plaintext has been recovered and no cipher family is rejected here. '
             'Page-associated vocabulary also appears in Currier A. In these matched herbal samples '
             'it is weaker than in B. In B most measured association belongs to types appearing at '
             'least five times in the panel. A model concerned only with rare ingredient names '
             'would therefore miss much of the pattern it needs to explain.')
    report.h('The manuscript comparison')
    report.p('Sixteen distinct herbal folios per Currier group, 64 clean tokens per page. '
             'Classifications come from ZL. IT2a is matched by page, not by individual glyph. '
             'Split and joined doubtful-space arms use their own first 64 clean tokens. '
             'Values are bits per apparent token above a within-section permutation baseline; '
             'the second column also conditions on line/paragraph roles. They are not percentages decrypted.')
    report.table(['Panel', 'Section excess', 'Role excess', 'Count 2–4 contribution', 'Count ≥5 contribution'], [
        [name, f"{r['section']['total']['excess']:.4f}", f"{r['roles']['total']['excess']:.4f}",
         f"{r['section']['bins']['count2to4']['excess']:.4f}",
         f"{r['section']['bins']['count5plus']['excess']:.4f}"]
        for name, r in manuscript.items() if name.endswith('_full')])
    report.p('Every first-eight and last-eight panel has positive excess under both conditionings '
             'in both transcriptions and spacing arms. This is directional replication under a '
             'fixed sampling rule, not a calibrated significance or family-acceptance claim. '
             'The A/B magnitude contrast may also reflect scribes, material and sampled pages. '
             'IT split/join outputs coincide on these selected spans; those arms are not independent confirmations.')
    report.table(['Half-panel', 'Section excess', 'Role excess'], [
        [name, f"{r['section']['total']['excess']:.4f}", f"{r['roles']['total']['excess']:.4f}"]
        for name, r in manuscript.items() if '_ZL_split_' in name and not name.endswith('_full')])
    report.h('Frequency is not meaning')
    report.p('Each type is assigned by its total panel count: once, 2–4 times, or at least five '
             'times. Each group contributes to the same overall score; we do not recompute MI '
             'on a filtered subset. All contributions and token masses are in evidence.json. '
             'There is no rank cutoff or tie-breaking. These frequency bins stay unchanged under '
             'the null permutations, eliminating the earlier position-dependent selection artifact.')
    b = manuscript['B_ZL_split_full']['section']
    original = manuscript['previous_ZL_original']['section']
    report.p(f"Types with ≥5 occurrences account for {b['bins']['count5plus']['excess']/b['total']['excess']:.1%} "
             f"of section excess in the full B herbal panel and "
             f"{original['bins']['count5plus']['excess']/original['total']['excess']:.1%} in the earlier "
             'herbal/biological panel. This is a share of a corrected statistic, not a share of '
             'semantic content. The ≥5 bin is broad: repeated content words can belong to it, '
             'and we have not identified function words. A lower relative rare-bin contribution '
             'does not demonstrate a page-state mechanism.')
    report.p('A singleton has no repeat with which to estimate a page preference. With equal-size '
             'pages its corrected contribution is exactly zero. It could still be a perfectly '
             'meaningful plant name. The statistic cannot answer that question. After role '
             'conditioning unequal margins can alter the zero identity; inspect the stored decomposition.')
    report.h('Comparison with the frozen source passages')
    report.p('These are the twelve existing stage-28 plaintext panels, not newly selected best fits. '
             'Recipe and medical texts also place some association in frequent types. Their '
             'variation cautions against inferring genre from the aggregate manuscript profile. '
             'No source/function-word lexicon or semantic classifier was introduced.')
    report.table(['Passage', 'Section excess', '2–4 contribution', '≥5 contribution'], [
        [name, f"{r['section']['total']['excess']:.4f}",
         f"{r['section']['bins']['count2to4']['excess']:.4f}",
         f"{r['section']['bins']['count5plus']['excess']:.4f}"]
        for name, r in evidence['reference'].items()])
    report.h('What changes next')
    report.p('Retain word/mixed codes as open hypotheses. Give common recurring types an explicit '
             'role in the next model, and keep A/B separate. Before fitting persistent choices, '
             'construct a bounded glyph-slot codebook, count unique outputs and collisions, '
             'and compare it with R2 on frozen pages. Round-trip recovery is a necessary engineering '
             'check; it is not manuscript evidence. Neither shuffle sensitivity nor a page-association '
             'match alone distinguishes language from a sequential message-free generator.')
    report.link('Decisions for the next codebook study', '../../docs/guides/CONTEXT_CODEBOOK_GUARDRAILS.md')
    report.p('The suggested 1,500–4,500-entry codebook around 1420 is not established here. '
             'The historical survey and the limitation of its size categories are recorded separately; '
             'large-key simulations must remain explicitly unattested at that date.')
    report.link('Historical source check', '../../data/historical_cipher_sources/README.md')
    report.h('Calibration, uncertainty and reproduction')
    report.p(f"The 50 IID calibration panels averaged {calibration['iid_mean']:.6f} excess bits; "
             f"ten planted rare-repeat panels averaged {calibration['planted_mean']:.6f}. "
             'All gates passed before manuscript metrics. Additivity against the established '
             'scalar estimator, bijective renaming and the all-unique control passed. '
             'The ten planted cases vary null seeds, not the planted signal. No synthetic solver '
             'accuracy is being claimed.')
    report.p('199 permutations per measurement, seed 2901. Stored null SDs, quantiles and '
             'Monte Carlo SEs describe permutation variability only, not manuscript sampling '
             'uncertainty. The new seed produces small differences from stage 28; historical '
             'outputs were not changed. Eight-page halves also change type counts and bin membership, '
             'so they are sensitivity panels, not additive pieces of the full-panel decomposition.')
    report.p('Protocol committed at 3d4bdfc before execution. No protocol deviations or post hoc '
             'parameter changes. This stage fits no keys or generators. R2 comparison, glyph-slot '
             'construction and expanded manual label alignment remain upcoming work, not completed tests.')
    report.table(['Currier group', 'Selected herbal pages'], [
        [group, ', '.join(dict.fromkeys(r['page'] for r in slots[f'{group}_ZL_split_full']))]
        for group in ('A', 'B')])
    report.link('Frozen protocol', '../../docs/protocols/FREQUENCY_CURRIER_A_2026-10-09.md')
    report.link('Machine-readable evidence', 'evidence.json')
    report.link('Exact slots', 'slots.json')
    report.link('Source and environment manifest', 'manifest.json')
    report.p('All 215 software tests passed, including the separate PostgreSQL test database. '
             'Source and wheel builds passed; the CLI lists stages 01–29. Verification against '
             'the independent scalar estimator checks all 82 manuscript/reference totals, '
             'frequency additivity, manifest hashes and half-panel folio disjointness.')
    report.link('Verification output', 'verification.json')
    report.p('Reproduce into a new directory: uv run --locked python -m '
             'voynich.experiments.e29_frequency_currier_a --output results/<new-dir>; then '
             'uv run --locked python -m voynich.laboratory.frequency_report --directory results/<new-dir>.')
    report.p('Verify: uv run --locked python -m voynich.laboratory.frequency_verify '
             '--directory results/<new-dir>.')
    report.save(folder)
    html = folder/'report.html'
    html.write_text(html.read_text().replace('Voynich: unit size and parser audit', 'Voynich: frequency and Currier A'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'results/frequency_currier_a_2026-10-09')
    render(parser.parse_args().directory)


if __name__ == '__main__':
    main()
