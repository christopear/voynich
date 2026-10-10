"""Prepare exact-match coordinate candidates; never auto-assert image alignment."""
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
from voynich.paths import ROOT
from voynich.experiments.e27_unit_association import sha
from voynich.experiments.e28_word_homophones import save


def packet(root=ROOT):
    source=root/'results/crib_scope_2026-10-09/inventory.json';e=json.loads(source.read_text())
    by_locus={r['locus']:r for r in e['rows']};rows=[];hashes={str(source.relative_to(root)):sha(source)}
    crossing=[]
    for item in e['cross_page_exact_repeats']:
        sides={by_locus[l]['folio'] in {'f70','f71'} for l in item['loci']}
        if len(sides)==2:crossing.append(item)
        for locus in item['loci']:
            row=by_locus[locus];path=root/f"data/frontier/boxes/{row['page']}.js"
            vocabulary,boxes=json.loads(path.read_text());hashes[str(path.relative_to(root))]=sha(path)
            matches=[]
            for token in row['tokens']:
                ids={i for i,v in enumerate(vocabulary) if v[0]==token}
                matches.append(dict(token=token,candidates=[dict(index=i,box=b[1:]) for i,b in enumerate(boxes) if b[0] in ids]))
            rows.append(dict(locus=locus,page=row['page'],folio=row['folio'],label=row['tokens'],transcription=row['raw'],
                split='development' if row['folio'] in {'f70','f71'} else 'reserved',crosses_split=len(sides)==2,
                coordinate_matches=matches,status='unverified exact-spelling coordinate candidates',
                image_alignment=None,illustrated_referent=None))
    return dict(rows=rows,crossing_types=crossing,crossing_count=len(crossing),required_crossing_types=5,
        semantic_test_gate=len(crossing)>=5,hashes=hashes,
        warning='Coordinates use the upstream Voynichese grid, not Yale scan pixels; no inferred transformations or fuzzy spelling matches.')


def run(output):
    output.mkdir(parents=True,exist_ok=False);e=packet();save(output/'packet.json',e)
    rows=[]
    for r in e['rows']:
        counts=', '.join(f"{m['token']}: {len(m['candidates'])}" for m in r['coordinate_matches'])
        rows.append('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in [r['locus'],' '.join(r['label']),r['split'],r['crosses_split'],counts,r['transcription']])+'</tr>')
    body='<h1>Recurring-label alignment packet</h1><p>No translations or confirmed image alignments. There are '+str(e['crossing_count'])+' cross-split label types; the frozen minimum was five. The proposed semantic test cannot proceed unchanged.</p>'
    body+='<p>Exact spelling candidates below are aids to manual inspection, not validated bounding boxes. Missing matches show transcription/segmentation differences; multiple matches are unresolved. Coordinate scale is from Voynichese.com, not Yale pixels. No fuzzy matching was used.</p><p><a href="https://collections.library.yale.edu/catalog/2002046">Primary Yale facsimile</a> · <a href="packet.json">Full candidate coordinates and provenance</a></p>'
    body+='<table><tr>'+''.join('<th>'+s+'</th>' for s in ['Locus','Complete label','Split','Crosses split','Candidate boxes per token','ZL record'])+'</tr>'+''.join(rows)+'</table>'
    (output/'report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Label alignment packet</title><style>body{font:16px/1.5 system-ui;max-width:1200px;margin:35px auto;padding:25px;color:#203540}table{border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #ccc;text-align:left}th{background:#e8f0f2}</style>'+body+'</html>')
    (output/'README.md').write_text('''# Recurring-label alignment packet

Preparation only; no semantic fitting. Exact coordinate candidates are in
`packet.json` and [the review table](report.html). Four label types cross the
original folio split: otaly, okeoly, okydy, okaram. The scope required five;
therefore its semantic test gate fails before fitting. Do not lower it post hoc.

All 22 recurring types are included for manual alignment. Exact matches to the
cached Voynichese coordinate vocabulary are candidates only, not confirmation
that a box belongs to the same ZL locus or illustrated figure. Missing matches
are retained; no fuzzy equivalences invented. Coordinates are not Yale pixels.
No source drawings or lexical meanings have been assigned automatically.

Producer: `python -m voynich.laboratory.label_alignment_packet --output results/<new-dir>`.
Source and coordinate hashes are in the packet; coordinate provenance is in
`data/frontier/README.md`. The original glyph/image alignment remains to be
completed before a new semantic protocol can be considered.
''')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'results/label_alignment_2026-10-09')
    run(p.parse_args().output)


if __name__=='__main__':main()
