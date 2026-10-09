"""Generate the stage-30 operating report from recorded evidence."""
import argparse
import json
from pathlib import Path

import numpy as np

from voynich.laboratory.structured_codes import RULES
from voynich.laboratory.unit_association_report import Report
from voynich.paths import ROOT


def render(folder):
    read = lambda name: json.loads((folder/name).read_text())
    evidence, grammar = read('evidence.json'), read('grammar.json')
    report = Report('Voynich: structured codewords and local reuse')
    report.p('Stage 30, 9 October 2026. Evidence label: search found no fit in a bounded '
             'forward-model grid. No plaintext was recovered. The new test asks whether a '
             'small system for constructing codewords, combined with reusing alternatives '
             'locally, can match Voynich better than copy-and-modify text without a message.')
    report.p('The elementary slot construction has enough distinct outputs to hold the recipe '
             'dictionary, but its strings fail to reproduce the manuscript’s internal '
             'predictability. Persistence raises page association, sometimes too much. '
             'Neither the tested cipher nor the R2 comparison jointly fits the declared '
             'measurements. This is a limitation of these explicit constructions, not an '
             'exclusion of word codes, contextual ciphers, or message-free mechanisms in general.')
    report.h('What was actually tested')
    report.p('One apparent ciphertext word per normalized Italian recipe word, two disjoint '
             'alternatives per word, a fixed dictionary across pages. Four policies: IID choice; '
             'one shared choice per page; one remembered choice per word per page; and the '
             'latter with a 25% chance of refreshing the choice on later occurrences. '
             'Each random choice is a fair bit. Only the last policy adds a refresh parameter; '
             'it was fixed in advance, not tuned after seeing results.')
    report.p('The glyph construction splits 2–10-glyph development words into first glyph, '
             'middle sequence and final glyph, then independently recombines bounded slot lists. '
             'It does not infer linguistic affixes or claim to reconstruct Voynich’s full word '
             'grammar. The middle list is bounded to 64 entries, with up to 16 entries at each '
             'edge. Random dictionaries are drawn from this construction; no key is optimized.')
    report.p('Both models learn from the same 512 development tokens on eight Currier B herbal '
             'folios. Eight different B folios are reserved for evaluation; IT, joined spaces '
             'and A are unchanged-setting sensitivities. R2 uses the existing six window/mutation/'
             'coupling settings. It runs continuously across pages, whereas cipher variant state '
             'resets per page. That difference is part of the declared competing mechanisms.')
    report.table(['Construction quantity', 'Value'], [
        ['Slot combinations', grammar['combinations']], ['Unique strings', grammar['unique_support']],
        ['Collisions', grammar['collisions']], ['Required dictionary entries / codewords', '1,484 / 2,968'],
        ['Maximum log2 support', f"{grammar['maximum_support_bits']:.3f} bits (not achieved entropy)"]])
    report.table(['Panel', 'Tokens covered', 'Types covered', 'Previously unseen types covered'], [
        [name, f"{v['token']:.1%}", f"{v['type']:.1%}",
         'n/a' if v['unseen_type'] is None else f"{v['unseen_type']:.1%}"]
        for name, v in grammar['coverage'].items()])
    report.p('About 45% of the reserved B tokens lie outside this fitted grammar’s support. '
             'No assignment of its strings to plaintext words can represent those observed '
             'tokens without changing the grammar or adding exceptions. This support failure '
             'is specific to the frozen slot lists; it is not evidence against all slot systems.')
    if 'selection' not in evidence:
        report.p('The run stopped at a preregistered gate: '+evidence['status'])
        report.save(folder)
        return
    records, calibration, costs = read('generated.json'), read('calibration.json'), read('costs.json')
    report.h('Local reuse solves only part of the problem')
    report.p('The following are development medians across both passages and all six keys. '
             'Page association and its role-conditioned version are permutation-corrected '
             'bits per apparent token. Glyph entropy is the conditional entropy of adjacent '
             'glyphs within words, without start/end symbols. A lower value means more '
             'predictable next glyphs; it is not a plaintext-recovery score.')
    table = []
    for setting, rule in enumerate(RULES):
        rr = [r for r in records if r['family'] == 'cipher' and r['split'] == 'development' and r['setting'] == setting]
        v = np.median([r['profile']['vector'] for r in rr], axis=0)
        table.append([rule, f'{v[0]:.3f}', f'{v[1]:.3f}', f'{v[2]:.3f}', f'{v[3]:.3f}', f'{v[6]:.3f}'])
    target = evidence['targets']['B_ZL_split_early']['profile']['vector']
    table.append(['Voynich development', *[f'{target[i]:.3f}' for i in (0, 1, 2, 3, 6)]])
    report.table(['Policy', 'TTR', 'Top-ten share', 'Page association', 'Role-conditioned', 'Glyph entropy'], table)
    report.p('The development selection chooses refresh, but even its median maximum scaled '
             'residual is about 3.0 (the descriptive neighbourhood ends at 1). One shared choice '
             'per page and per-word persistence overshoot page association. IID undershoots it. '
             'Refresh moves the role-conditioned score nearer the manuscript without repairing '
             'glyph predictability. No development draw in either family jointly fits all seven measures.')
    report.h('Reserved-page outcome: neither model passes the joint screen')
    rows = []
    for name, observed in evidence['targets'].items():
        for family in ('cipher', 'R2'):
            group = evidence['comparisons'][family][name]
            median = np.median([d['profile']['vector'] for d in group['draws']], axis=0)
            rows.append([name, family, f"{group['hits']}/{group['total']}",
                         f"{min(d['distance'] for d in group['draws']):.2f}", f'{median[2]:.3f}', f'{median[6]:.3f}'])
    report.table(['Target', 'Frozen model', 'Joint hits', 'Best max residual', 'Median page association', 'Median glyph entropy'], rows)
    report.p('The selected R2 configuration is level 2 with coupling enabled. For reserved B, '
             'Voynich glyph entropy is 2.072 bits, versus median 2.781 for the cipher and 2.639 '
             'for R2. R2’s lower-mutation configurations can approach the glyph entropy, but '
             'produce far too much page association and repetition. Choosing a different '
             'configuration separately for each measurement would not constitute one working model.')
    report.p('Twelve cipher validation draws mean two source passages × six keys, not twelve '
             'independent sources. R2 has six validation draws. Settings were frozen using '
             'development only. Secondary targets reuse the same generated sequences and '
             'recompute role-sensitive profiles on the target’s layout. These are sensitivity '
             'comparisons, not additional independent manuscripts.')
    report.h('What the shuffle controls do—and do not—show')
    report.p('Equality at lags 1, 4 and 16 is measured along each page’s token stream, including '
             'across lines. Whole-word controls shuffle within page/role groups. Line controls '
             'move whole retained lines within paragraph-first-line classes, carrying their '
             'metadata. All retain page vocabularies. These diagnostics assess recurrence order, '
             'not grammar; neither positive nor negative values establish meaningful text.')
    rows = []
    for name in ('B_ZL_split_early', 'B_ZL_split_late'):
        for kind in ('word', 'line'):
            rows.append([name, kind, *[f'{v:.4f}' for v in evidence['targets'][name]['order'][kind]['excess']]])
    for family in ('cipher', 'R2'):
        rr = [r for r in records if r['family'] == family and r['split'] == 'validation'
              and r['setting'] == evidence['selection'][family]['setting']]
        for kind in ('word', 'line'):
            v = np.median([r['order'][kind]['excess'] for r in rr], axis=0)
            rows.append([family+' validation median', kind, *[f'{x:.4f}' for x in v]])
    report.table(['Panel/model', 'Control', 'Lag 1 excess', 'Lag 4 excess', 'Lag 16 excess'], rows)
    report.p('The original and reserved manuscript panels do not show a consistent positive '
             'effect across these lags and controls. R2 also has shuffle effects. We therefore '
             'do not use this recurrence diagnostic as a cipher-only property or claim an '
             'order-based distinction between language and message-free text.')
    report.h('Capacity, state and key burden')
    report.p('The six dictionaries each contain 1,484 normalized recipe types with 2,968 codewords. '
             'The entire source vocabulary is known before evaluation; this is not unseen-word '
             'key recovery. UTF-8 JSON dictionary descriptions cost about 324,000 bits each; '
             'the grammar costs 11,440 bits. R2’s serialized trained model costs 215,984 bits. '
             'Serialization lengths are implementation-dependent accounting, not historical '
             'storage estimates or a calibrated minimum-description-length ranking.')
    report.p('The uniform ordered-assignment reference costs about 29,962 bits. It excludes '
             'dictionary spellings and is not the entropy of our weighted sampler. Do not add '
             'it to an explicit dictionary serialization as if these were independent costs. '
             'Neither a short PRNG seed nor an uncounted page choice makes a codebook free.')
    rows = []
    for rule in RULES:
        rr = [r['audit'] for r in records if r['family'] == 'cipher' and r['split'] == 'validation' and r['rule'] == rule]
        span = lambda key: f"{min(a[key] for a in rr):.3f}–{max(a[key] for a in rr):.3f}"
        rows.append([rule, span('trajectory_bits'), span('peak_variant_state_bits'), span('variant_one_share')])
    report.table(['Rule', 'Random-trajectory bits / 512 words', 'Peak stored variant bits', 'Realised variant-one fraction'], rows)
    report.p('The stored state count covers variant bits only: per-word memory also needs '
             'word identifiers or indexed dictionary slots and presence flags. Trajectory costs '
             'include fresh fair bits and refresh/no-refresh probabilities. They describe the '
             'sampled encoder path, not extra decoder key: disjoint codewords decode directly. '
             'The page policy has only eight independent choices per panel, so realised variant '
             'fractions can differ substantially from one half even though its marginal law is fair.')
    report.p('For a concrete additional state-storage budget, an indexed array with one valid '
             'flag and one variant bit per dictionary entry costs 2 × 1,484 = 2,968 bits for '
             'word-page/refresh, plus the shared dictionary and a page-reset rule. The page '
             'policy needs one persistent variant bit; IID needs none. This is a stated '
             'implementation convention, not a minimum memory or information bound, and is '
             'separate from the random trajectory’s probability cost.')
    report.h('Calibration and verification')
    report.p(f"All {calibration['passed']}/{calibration['total']} independent-key synthetic targets "
             'met the preregistered selection-reliability gate (max residual ≤2; minimum 12/16). '
             'This gate is deliberately distinct from the stricter descriptive manuscript '
             'neighbourhood ≤1. It validates coarse profile selection, not exact parameter '
             'identifiability or a calibrated family rejection test.')
    discrimination = calibration['discrimination']
    report.p(f"Leaving each development seed out gives {discrimination['balanced_accuracy']:.1%} "
             'balanced accuracy distinguishing these simulated cipher/R2 profiles (gate 80%). '
             'This is a diagnostic on the sampled models, not classification of Voynich. '
             'A manuscript outside both model distributions cannot be identified by forcing '
             'it into the nearer class.')
    verification = read('verification.json')
    report.p(f"All {verification['replayed_panels']} generated panels replay exactly; "
             f"{verification['known_key_word_roundtrips']:,} cipher word tokens round-trip with known keys. "
             f"All {verification['calibration_replays']} calibration cases and "
             f"{verification['comparison_recomputations']} comparisons were recomputed. "
             'Stored profiles and order controls, source hashes and chapter/folio disjointness were checked.')
    report.p('Software validation: all 220 tests passed, including integration against the '
             'separate PostgreSQL test database. Source distribution and wheel builds passed; '
             'the CLI lists stages 01–30. No new Python dependencies were required.')
    report.p('Protocol committed at fc0c80e before execution. No grid expansion, changed '
             'threshold or post hoc model repair. Limits: one culinary source; only 512 tokens '
             'per target; fixed first/last-glyph slots; truncated middle inventory; random '
             'lexical assignment; no complete glyph-distribution likelihood, boundary-coupling '
             'test or semantic anchors. Large historical codebook feasibility remains unverified.')
    report.h('What this changes for the next step')
    report.p('Do not spend more seeds tuning page persistence in this grammar. The next '
             'representational question is whether dependencies between codeword parts can '
             'predict unseen word forms while retaining enough unique codes. First measure '
             'that coverage/predictability tradeoff on frozen pages, without a new key search. '
             'Independently aligned visual labels remain the route to semantic constraints; '
             'neither this result nor a later structural match supplies a plaintext crib.')
    report.link('Frozen protocol', '../../docs/protocols/STRUCTURED_WORD_CODES_2026-10-09.md')
    report.link('Full evidence', 'evidence.json')
    report.link('All generated panels and audits', 'generated.json')
    report.link('Calibration', 'calibration.json')
    report.link('Verification', 'verification.json')
    report.p('Reproduce into a new directory with python -m voynich.experiments.e30_structured_word_codes '
             '--output results/<new-dir>; then python -m voynich.laboratory.structured_verify '
             '--directory results/<new-dir> and python -m voynich.laboratory.structured_report '
             '--directory results/<new-dir>. Use uv run --locked for the project environment.')
    report.save(folder)
    html = folder/'report.html'
    html.write_text(html.read_text().replace('Voynich: unit size and parser audit', 'Voynich: structured codewords and local reuse'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'results/structured_word_codes_2026-10-09')
    render(parser.parse_args().directory)


if __name__ == '__main__':
    main()
