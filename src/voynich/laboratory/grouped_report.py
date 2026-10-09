"""Render the bounded grouped-code evidence without running new searches."""
import argparse
from collections import defaultdict
import html
import json
from pathlib import Path

from voynich.storage.artifacts import read_json, write_json


def compare(evidence):
    rows=evidence['rows']; calibration=[]; comparisons=[]; stability=[]
    for r in rows:
        if r['kind']!='synthetic':continue
        c=r['calibration'];accuracy=(c['recovery'] or {}).get('nonspace_edit_accuracy')
        oracle_rank=next((i+1 for i,p in enumerate(r['screening']['survivors']) if p['prefixes']==c['oracle_prefixes']),None)
        calibration.append({'id':r['id'],'language':r['language'],'spacing':r['spacing'],'seed':r['seed'],
            'nonspace_accuracy':accuracy,'space_boundary_f1':c['space_boundary_f1'],
            'oracle_policy_shortlisted':c['oracle_policy_shortlisted'],'oracle_screen_rank':oracle_rank,
            'oracle_loss':c['oracle_loss'],'selected_loss':r['selected']['loss'] if r['selected'] else None,'roundtrip':c['known_key_roundtrip'],
            'gate_pass':accuracy is not None and accuracy>=.9})
    for spacing in ('preserve','encoded'):
        originals=[r for r in rows if r['kind']=='voynich' and r['control']=='original' and r['spacing']==spacing]
        for original in originals:
            for c in rows:
                if c['kind']!='voynich' or c['control']=='original' or c['spacing']!=spacing or c['seed']!=original['seed']:continue
                comparable=original['selected'] is not None and c['selected'] is not None
                comparisons.append({'spacing':spacing,'seed':original['seed'],'control':c['control'],
                    'comparable':comparable,'original_lower_loss':original['selected']['loss']<c['selected']['loss'] if comparable else None,
                    'original_lower_independent_cost':original['language_metrics']['pliny']<c['language_metrics']['pliny'] if comparable else None})
        if len(originals)==2 and all(r['selected'] for r in originals):
            a,b=[r['selected'] for r in originals]
            same=a['policy']['prefixes']==b['policy']['prefixes']
            common=set(a['payload']['table'])&set(b['payload']['table'])
            matches={c:a['payload']['table'][c] for c in sorted(common) if a['payload']['table'][c]==b['payload']['table'][c]}
            stability.append({'spacing':spacing,'same_prefix_policy':same,'shared_code_types':len(common),
                              'matching_emissions':matches,'matching_fraction':len(matches)/len(common) if common else None,
                              'interpretation':'Mapping agreement only; neither readings nor chance calibration.'})
    return {'calibration':calibration,'controls':comparisons,'stability':stability,
            'registered_runs':len(evidence['stages']),'evaluations':evidence['registered_evaluations'],
            'exceptions':sum(s['failures'] for s in evidence['stages']),
            'calibration_gate_passes':sum(c['gate_pass'] for c in calibration)}


def render(evidence,out):
    summary=compare(evidence);out.mkdir(parents=True,exist_ok=True)
    def esc(x):return html.escape('—' if x is None else ('Yes' if x is True else 'No' if x is False else str(x)))
    def num(x):return '—' if x is None else f'{x:.3f}'
    def pct(x):return '—' if x is None else f'{100*x:.1f}%'
    def table(headers,rows):
        return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
    original=[r for r in evidence['rows'] if r['kind']=='voynich' and r['control']=='original']
    parts=['<h1>Grouped codes: returning to Voynich</h1>',
        '<p class="lead">This tests a different representation: one- and two-glyph codes, with preserved or encoded word spaces. Lower language costs are not percentages decrypted.</p>',
        f'<p><strong>Calibration: {summary["calibration_gate_passes"]}/{len(summary["calibration"])} cases reached 90% blind nonspace recovery.</strong> Failed calibration prevents a negative manuscript result from rejecting this family. This pilot does not establish a decipherment.</p>',
        '<h2>Actual Voynich: f26r</h2>',
        '<p>Both spacing arms enumerate the same bounded prefix family. A dash means no structurally admissible policy, not a failed key search. Counts concern this grid only. All retained glyphs are consumed; uncertain omissions and drawings break spans.</p>']
    if not any(r['selected'] for r in original):
        parts.append('<p><strong>No original-page policy survived the declared parsing and expansion constraints. No f26r plaintext was selected and no original-key transfer to f31r/f39v could be performed.</strong> This is a bounded structural result, not a rejection of grouped codes generally.</p>')
    parts.append(table(['Spacing','Seed','Surviving policies','Searched policies','Selection loss','Independent Pliny bits/char'],[
        (r['spacing'],r['seed'],r['screening']['counts']['surviving'],len(r['runs']),num(r['selected']['loss'] if r['selected'] else None),num(r.get('language_metrics',{}).get('pliny'))) for r in original]))
    parts+=['<h2>Matched controls</h2>','<p>Whole-word, symbol, and two paragraph/line-role-stratified word shuffles receive the full screening pipeline. Each surviving shortlisted policy receives 4,096 proposals. Different survivor counts mean different total search budgets; this is not an equal-total-budget comparison. These repeated comparisons are not p-values.</p>']
    parts.append(table(['Spacing','Control','Structural survivors','Searches across both seeds'],[(spacing,control,next(r['screening']['counts']['surviving'] for r in evidence['rows'] if r['kind']=='voynich' and r['spacing']==spacing and r['control']==control),sum(len(r['runs']) for r in evidence['rows'] if r['kind']=='voynich' and r['spacing']==spacing and r['control']==control)) for spacing in ('preserve','encoded') for control in ('original','word-shuffled','symbol-shuffled','layout-1','layout-2')]))
    if any(r['comparable'] for r in summary['controls']):
        parts.append(table(['Spacing','Seed','Control','Original lower fitted loss','Original lower independent cost'],[(r['spacing'],r['seed'],r['control'],r['original_lower_loss'],r['original_lower_independent_cost']) for r in summary['controls'] if r['comparable']]))
    else:
        parts.append('<p>No original-versus-control language comparison is available because no original parser survived. Surviving control decodings are exported for audit, not counted as manuscript evidence.</p>')
    parts+=['<h2>Frozen f31r / f39v transfer</h2>','<p>Neither parser nor key is refitted. Missing codes and invalid spans remain missing. Covered-run scores with different masks cannot establish comparative transfer improvement. Full-span scores include only spans decoded completely.</p>']
    transfer_rows=[(r['spacing'],r['seed'],p,pct(v['glyph_coverage']),pct(v['valid_span_fraction']),v['fully_known_span_characters'],num(v['fully_known_span_bits_per_character']),num(v['covered_run_bits_per_character'])) for r in original for p,v in r.get('transfer',{}).items()]
    if transfer_rows:
        parts.append(table(['Spacing','Seed','Page','Glyph coverage','Valid spans','Fully known output chars','Full-span bits/char','Covered-run bits/char'],transfer_rows))
        parts+=['<h2>Mapping stability across seeds</h2>', '<pre>'+esc(json.dumps(summary['stability'],ensure_ascii=False,indent=2))+'</pre>', '<h2>Full selected original-page outputs</h2>']
        for r in original:
            if r['selected']:parts.append('<details><summary>'+esc(r['id'])+'</summary><pre>'+esc(r['selected']['payload']['plaintext'])+'</pre></details>')
    else:
        parts.append('<p><strong>Not performed for original Voynich:</strong> there is no selected original-page key to transfer, compare across seeds, or present as a candidate reading.</p>')
    parts+=['<h2>Synthetic calibration — known text, separate from manuscript evidence</h2>',
        '<p>Two independent keys/search seeds per language/spacing arm. Latin uses Celsus training and Pliny target text; Italian uses disjoint passages of Dante (same-author limitation). Two homophones over 16 glyphs; these fixtures do not reproduce every manuscript property. Space-boundary F1 uses absolute nonspace offsets and becomes hard to interpret when letters or lengths are wrong.</p>']
    parts.append(table(['Case','Known-key roundtrip','True policy rank / shortlist','Blind nonspace accuracy','Boundary F1','90% gate'],[(r['id'],r['roundtrip'],str(r['oracle_screen_rank'])+' / '+('kept' if r['oracle_policy_shortlisted'] else 'discarded'),pct(r['nonspace_accuracy']),num(r['space_boundary_f1']),r['gate_pass']) for r in summary['calibration']]))
    discarded=sum(not r['oracle_policy_shortlisted'] for r in summary['calibration'])
    parts.append('<p><strong>The shortlist discarded the true parsing policy in '+str(discarded)+'/'+str(len(summary['calibration']))+' cases.</strong> This is a demonstrated failure of the unigram pruning rule. More key-search budget cannot recover a parser removed before search. Oracle scores are recorded after selection and did not change the protocol.</p>')
    parts+=['<h2>What this study can decide</h2>',
        '<p>It tests fixed prefix-determined codes of length one or two, at most three long-code prefixes (plus fixed-width two), maximum two homophones, and expansion 1.35–2.00. This is not all grouped or variable-length coding. Preserved-space failures do not exclude grouping with different boundary or code-length rules. No separate test of full page-topic compatibility has been passed.</p>',
        '<p>The correction to the entropy screen retains a substantial reference-profile gap, while withdrawing universal exclusions and the unjustified one-bit allowance. The reported 7–10× reference-spread comparison does not apply to the complete five-source panel; short Italian/German texts drop out at larger block sizes.</p>',
        '<h2>Execution and provenance</h2>',f'<p>{summary["registered_runs"]} registered runs; {summary["evaluations"]:,} candidate evaluations; {summary["exceptions"]} evaluator exceptions. Each selected output was replayed exactly. See the export for all shortlisted policies, control outputs, known-key audits, data hashes and execution specifications.</p>',
        '<p><a href="evidence.json">Evidence</a> · <a href="comparisons.json">Comparisons</a> · <a href="specifications.json">Specifications</a> · <a href="environment.json">Execution environment</a> · <a href="README.md">Research decision</a></p>']
    body='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Grouped-code Voynich study</title><style>body{font:17px/1.55 system-ui,sans-serif;color:#172532;background:#f5f4ef;margin:0}main{max-width:1100px;margin:40px auto;padding:32px;background:white;border-radius:12px}h1{font-size:36px;line-height:1.2}h2{margin-top:36px;color:#173c46}.lead{font-size:21px}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;border-bottom:1px solid #dde4e5;text-align:left}th{background:#eaf1f2}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.6 monospace;background:#f0f3f3;padding:18px}details{margin:12px 0}a{color:#075866}</style><main>'+''.join(parts)+'</main></html>'
    for path,value in ((out/'comparisons.json',summary),):
        if path.exists():
            if read_json(path)!=value:raise ValueError('refusing changed evidence overwrite')
        else:write_json(path,value)
    path=out/'report.html'
    if path.exists() and path.read_text()!=body:raise ValueError('refusing changed report overwrite')
    path.write_text(body)
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();render(read_json(args.input),args.output)


def structural_envelope(spans, spacing):
    """Post-hoc diagnostic: largest expansion among fully parsable grid policies.

    Does not refit keys or relax the prospective threshold. This isolates how
    much the 1.35 cutoff mattered; it is not a new family-selection result.
    """
    from itertools import combinations
    from voynich.search.grouped import parse_span
    alphabet=sorted(set(''.join(spans))-{' '})
    policies=[p for n in (1,2,3) for p in combinations(alphabet,n)]+[tuple(alphabet)]
    valid=[]
    for prefixes in policies:
        try:tokens=[c for s in spans for c in parse_span(s,prefixes,spacing) if c!=' ']
        except ValueError:continue
        valid.append({'prefixes':list(prefixes),'expansion':sum(map(len,tokens))/len(tokens),
                      'inventory':len(set(tokens))})
    return {'spacing':spacing,'valid_policies':len(valid),
            'maximum_expansion':max(valid,key=lambda r:(r['expansion'],r['prefixes'])) if valid else None,
            'status':'Post-hoc structural diagnostic; no new key searches or threshold changes.'}
