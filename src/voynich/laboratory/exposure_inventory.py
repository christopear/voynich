"""Inventory of which manuscript pages earlier work has used, and how (10 October 2026).

No statistics on manuscript text are computed here beyond token counts. Each
rule names the stages, the role and whether the page set is read from stored
panels/code ("code") or from the stage documentation ("documentation").
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re

from voynich.experiments.e06_boundary_frontier import load_lines
from voynich.experiments.e27_unit_association import sha
from voynich.paths import ROOT

ZL = ROOT/'data/ZL3b-n.txt'
TIERS = {1: 'whole-manuscript descriptive statistics only',
         2: 'pooled statistics or model training within a language/section pool',
         3: 'targeted development, fitting or annotation panel',
         4: 'targeted evaluation, reserved or solver-target panel'}


def page_metadata():
    meta, order = {}, []
    for raw in ZL.read_text().splitlines():
        m = re.match(r'^<(f[^.> ]+)>\s*<!([^>]*)>', raw)
        if m:
            meta[m[1]] = dict(re.findall(r'\$(\w)=([^\s>]+)', m[2]))
            order.append(m[1])
    tokens = Counter()
    for ln in load_lines(ZL):
        tokens[ln['page']] += sum(w['clean'] for w in ln['words'])
    return {p: dict(page=p, folio=(re.match(r'f\d+', p) or re.match(r'f\w+', p))[0], section=meta[p].get('I'), currier=meta[p].get('L'),
                    hand=meta[p].get('H'), quire=meta[p].get('Q'), bifolio=meta[p].get('B'),
                    clean_paragraph_tokens=tokens[p]) for p in order}


def _pages(obj, known, acc):
    if isinstance(obj, dict):
        for value in obj.values():
            _pages(value, known, acc)
    elif isinstance(obj, list):
        for value in obj:
            _pages(value, known, acc)
    elif isinstance(obj, str):
        head = obj.split('.')[0]
        if head in known:
            acc.add(head)
    return acc


def panel_pages(path, known, keys=None):
    data = json.loads(path.read_text())
    if keys is not None:
        data = {k: data[k] for k in keys}
    return _pages(data, known, set())


def rules(pages):
    known = set(pages)
    r = ROOT/'results'
    slots29 = r/'frequency_currier_a_2026-10-09/slots.json'
    slots28 = r/'word_homophones_2026-10-09/slots.json'
    herbal_a1 = {p for p, m in pages.items() if (m['section'], m['currier'], m['hand']) == ('H', 'A', '1')}
    b_pages = {p for p, m in pages.items() if m['currier'] == 'B'}
    reserved_folios = set(json.loads((r/'word_shapes_2026-10-09/training.json').read_text())['reserved_folios'])
    broad = {p for p in b_pages if pages[p]['folio'] not in reserved_folios}
    with_text = {p for p, m in pages.items() if m['clean_paragraph_tokens'] > 0}
    return [
        dict(rule='whole_manuscript_statistics', tier=1, basis='code', pages=with_text,
             stages='6-8 boundary frontier, 12 reconstruction counts, 19-23 v101 mapping and variant tests',
             note='All paragraph text was read for structural statistics and transcription comparison.'),
        dict(rule='herbal_A_hand1_pool', tier=2, basis='code', pages=herbal_a1,
             stages='1-3 terminal sandhi, segmenter, lattices; 12 reconstruction',
             note='select_pages(section=H, currier=A, hand=1).'),
        dict(rule='currier_B_pool', tier=2, basis='documentation', pages=b_pages,
             stages='9-11 mechanism benchmark, 13-18 equivalence and coupling tests, 24-25 cipher families, capacity screen',
             note='Stage reports describe Currier B pools/folds; individual page roles within folds are not separated here.'),
        dict(rule='stage31_broad_training', tier=2, basis='code', pages=broad,
             stages='31-34 word-shape model, R2 training, edge-lift table',
             note='All clean Currier B tokens off the reserved folios trained the shape model and lift table.'),
        dict(rule='page_search_fit', tier=4, basis='documentation', pages={'f26r'} & known,
             stages='26 page pilot, line rotation, phase initialisation, grouped boundary',
             note='Key-search target page.'),
        dict(rule='page_search_transfer', tier=4, basis='documentation', pages={'f31r', 'f39v'} & known,
             stages='26 page pilot and follow-ups', note='Frozen-key transfer pages.'),
        dict(rule='stage27_panel', tier=3, basis='code', stages='27 unit association',
             pages=panel_pages(r/'unit_association_2026-10-09/manuscript_slots.json', known), note='16 Currier B folios.'),
        dict(rule='stage28_development', tier=3, basis='code', stages='28 word homophones',
             pages=panel_pages(slots28, known, ['ZL_original', 'ZL_joined', 'IT_original']), note='Original panel.'),
        dict(rule='stage28_additional', tier=4, basis='code', stages='28 word homophones',
             pages=panel_pages(slots28, known, ['ZL_additional', 'IT_additional']), note='Additional evaluation folios.'),
        dict(rule='stage29_A_panel', tier=3, basis='code', stages='29 frequency and Currier A; 31 scribe control',
             pages=panel_pages(slots29, known, ['A_ZL_split_full']), note='16 herbal A folios.'),
        dict(rule='stage29_B_panel', tier=3, basis='code', stages='29 frequency and Currier A; 31 scribe control',
             pages=panel_pages(slots29, known, ['B_ZL_split_full']), note='16 herbal B folios.'),
        dict(rule='stage30_34_development', tier=3, basis='code', stages='30-34 forward screens and correction',
             pages=panel_pages(slots29, known, ['B_ZL_split_early']), note='Selection target.'),
        dict(rule='stage30_34_reserved_B', tier=4, basis='code', stages='30-34 forward screens and correction',
             pages=panel_pages(slots29, known, ['B_ZL_split_late']),
             note='Reserved target; informed four successive hypotheses.'),
        dict(rule='stage30_34_A_transfer', tier=4, basis='code', stages='30-34 forward screens and correction',
             pages=panel_pages(slots29, known, ['A_ZL_split_late']), note='Currier A sensitivity target.'),
        dict(rule='label_packet', tier=3, basis='code', stages='label alignment and crib scope',
             pages=panel_pages(r/'label_alignment_2026-10-09/packet.json', known) |
             panel_pages(r/'crib_scope_2026-10-09/inventory.json', known),
             note='Label inventory and coordinate candidates; labels, not paragraph text.'),
    ]


def build():
    pages = page_metadata()
    listing = rules(pages)
    roles = defaultdict(list)
    for rule in listing:
        for page in rule['pages']:
            roles[page].append(rule['rule'])
    tier_of = {rule['rule']: rule['tier'] for rule in listing}
    rows = []
    for page, meta in pages.items():
        tier = max((tier_of[r] for r in roles[page]), default=0)
        rows.append(dict(meta, roles=sorted(roles[page]), tier=tier))
    herbal = [r for r in rows if r['section'] == 'H']
    summary = Counter((r['currier'], r['hand'], r['tier']) for r in herbal)
    groups = defaultdict(list)
    for r in herbal:
        groups[(r['quire'], r['bifolio'])].append(r)
    bifolios = [dict(quire=q, bifolio=b, pages=[r['page'] for r in rs], curriers=sorted({r['currier'] for r in rs}),
                     hands=sorted({r['hand'] for r in rs}), max_tier=max(r['tier'] for r in rs),
                     tokens=sum(r['clean_paragraph_tokens'] for r in rs)) for (q, b), rs in groups.items()]
    return dict(
        tiers=TIERS,
        rules=[dict({k: v for k, v in rule.items() if k != 'pages'}, pages=sorted(rule['pages'])) for rule in listing],
        pages=rows,
        herbal_summary=[dict(currier=c, hand=h, tier=t, pages=n) for (c, h, t), n in sorted(summary.items(), key=str)],
        herbal_bifolios=bifolios,
        counts=dict(pages=len(rows), herbal_pages=len(herbal), herbal_bifolios=len(bifolios),
                    herbal_bifolios_by_max_tier=dict(sorted(Counter(b['max_tier'] for b in bifolios).items()))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/exposure_inventory_2026-10-10')
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=False)
    inventory = build()
    inventory['hashes'] = {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), ZL]}
    (output/'inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=1) + '\n')
    with (output/'herbal_pages.csv').open('w', newline='') as stream:
        fields = ['page', 'folio', 'quire', 'bifolio', 'currier', 'hand', 'clean_paragraph_tokens', 'tier', 'roles']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in inventory['pages']:
            if row['section'] == 'H':
                writer.writerow({k: ';'.join(row[k]) if k == 'roles' else row[k] for k in fields})
    print(json.dumps(inventory['counts']))


if __name__ == '__main__':
    main()
