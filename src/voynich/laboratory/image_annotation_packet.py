"""Frozen page split and blank annotation templates for the image-feature feasibility pilot.

Reads only page metadata and the exposure inventory. It computes no text
statistic and no text-image association. Protocol:
docs/protocols/IMAGE_ANNOTATION_PILOT_2026-10-10.md.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path

from voynich.experiments.e27_unit_association import sha
from voynich.laboratory.exposure_inventory import build
from voynich.paths import ROOT

MIN_TOKENS = 40
FEATURES = ('leaf_division', 'leaf_arrangement', 'stem_branching', 'root_form', 'flower_presence', 'flower_form')
COVARIATES = ('plants_on_page', 'text_position', 'blue_pigment', 'red_pigment')
TEMPLATE_FIELDS = ('page', 'annotator', 'image_source', *FEATURES, *COVARIATES, 'confidence', 'notes')


def split(inventory):
    """Development = eligible pages on bifolios already used in a targeted panel; the rest alternate X/Y."""
    eligible = [p for p in inventory['pages']
                if (p['section'], p['currier'], p['hand']) == ('H', 'A', '1') and p['clean_paragraph_tokens'] >= MIN_TOKENS]
    order = {p['page']: i for i, p in enumerate(inventory['pages'])}
    tiers = defaultdict(int)
    for p in inventory['pages']:
        if p['section'] == 'H':
            key = (p['quire'], p['bifolio'])
            tiers[key] = max(tiers[key], p['tier'])
    groups = defaultdict(list)
    for p in eligible:
        groups[(p['quire'], p['bifolio'])].append(p['page'])
    ordered = sorted(groups, key=lambda g: min(order[p] for p in groups[g]))
    development, low = [], []
    for g in ordered:
        (development if tiers[g] >= 3 else low).append(g)
    sets = {'development': development, 'confirmation_X': low[0::2], 'confirmation_Y': low[1::2]}
    return dict(
        rule=dict(eligible='section H, Currier A, hand 1, at least %d clean paragraph tokens' % MIN_TOKENS,
                  group='bifolio = (quire, bifolio) from ZL page variables $Q and $B',
                  development='groups containing any herbal page with exposure tier >= 3',
                  confirmation='remaining groups in manuscript order, alternating X then Y'),
        sets={name: dict(bifolios=[list(g) for g in gs], pages=sorted((p for g in gs for p in groups[g]), key=order.get))
              for name, gs in sets.items()},
        counts={name: dict(bifolios=len(gs), pages=sum(len(groups[g]) for g in gs)) for name, gs in sets.items()},
        excluded_low_text=sorted(p['page'] for p in inventory['pages']
                                 if (p['section'], p['currier'], p['hand']) == ('H', 'A', '1')
                                 and p['clean_paragraph_tokens'] < MIN_TOKENS))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/image_annotation_pilot_2026-10-10')
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=False)
    result = split(build())
    result['hashes'] = {str(p.relative_to(ROOT)): sha(p) for p in
                        [Path(__file__), ROOT/'src/voynich/laboratory/exposure_inventory.py', ROOT/'data/ZL3b-n.txt']}
    (output/'split.json').write_text(json.dumps(result, indent=1) + '\n')
    for annotator in ('A', 'B'):
        with (output/f'development_template_{annotator}.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=TEMPLATE_FIELDS)
            writer.writeheader()
            for page in result['sets']['development']['pages']:
                writer.writerow(dict(page=page, annotator=annotator))
    print(json.dumps(result['counts']))


if __name__ == '__main__':
    main()
