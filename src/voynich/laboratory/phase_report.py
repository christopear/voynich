"""Manuscript-first report for the equal-budget initialization comparison."""
import argparse
from html import escape
from pathlib import Path
from statistics import mean

from voynich.storage.artifacts import read_json,write_json


def pair_rows(evidence):
    index={}
    for row in evidence['rows']:
        key=(row['case_id'],row['variant'])
        if key in index:raise ValueError('duplicate pipeline result')
        index[key]=row
    return [(index[(case,'cold')],index[(case,'separate-then-joint')]) for case in evidence['plan']['case_ids']]


def lexical_links(row):
    """Unique (phase, cipher word, proposed word), not repeated word tokens."""
    allowed=set(row['word_hits']['pliny']['distinct_hits']);key=row['candidate']['key'];links=set()
    for i,line in enumerate(row['lines']):
        for cipher in line.split():
            plain=''.join(key[chr(ord(c)+(i%2)*65536)] for c in cipher)
            if plain in allowed:links.add((i%2,cipher,plain))
    return links


def build(evidence,previous,output):
    pairs=pair_rows(evidence)
    if len(evidence['stages'])!=56 or evidence['registered_evaluations']!=229376:
        raise ValueError('study does not match the complete planned budget')
    prior={r['run_id']:r for r in previous['runs']}
    manuscript=[(a,b) for a,b in pairs if a['case']=='voynich']
    originals=[(a,b) for a,b in manuscript if a['control']=='original']
    synthetic=[(a,b) for a,b in pairs if a['case']=='synthetic']
    for a,b in manuscript:
        for page in a['transfer']:
            if a['transfer'][page]['unknown']!=b['transfer'][page]['unknown']:
                raise ValueError('transfer coverage masks differ between methods')
    def table(head,rows):
        return '<div class="scroll"><table><tr>'+''.join('<th>'+escape(str(v))+'</th>' for v in head)+'</tr>'+''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</table></div>'
    fmt=lambda x:f'{x:.3f}'
    pct=lambda x:f'{x:.1%}'
    comparisons=[{'case_id':a['case_id'],'case':a['case'],'control':a['control'],
                  'cold_loss':a['selected_loss'],'initialized_loss':b['selected_loss'],
                  'initialization_advantage':a['selected_loss']-b['selected_loss']} for a,b in pairs]
    stable=[]
    for variant in ('cold','separate-then-joint'):
        for control in ('original','line-shuffled-1','line-shuffled-2','line-shuffled-3','symbol-shuffled'):
            rows=[r for r in evidence['rows'] if r['case']=='voynich' and r['variant']==variant and r['control']==control]
            common=set.intersection(*(lexical_links(r) for r in rows))
            stable.append({'variant':variant,'control':control,'shared_links':sorted(common)})
    body='<h1>Did better search help on Voynich?</h1><p>Separate table initialization → joint refinement → immediate manuscript trial</p>'
    body+='<div class="summary"><p><strong>Actual Voynich and synthetic results are reported separately.</strong> No plaintext accuracy can be measured on Voynich. Fitted scores, control comparisons and frozen-page predictions are evidence to assess, not translations.</p>'
    body+=f'<p>At equal 8,192-evaluation budgets, separate initialization beats cold search on fitted loss in {sum(b["selected_loss"]<a["selected_loss"] for a,b in manuscript)}/10 manuscript/control cases and {sum(b["selected_loss"]<a["selected_loss"] for a,b in originals)}/2 original-page seeds.</p>'
    body+='<p>The four known-text checks show whether initialization improved recovery; they do not count as Voynich progress. Both methods were then tried immediately on f26r, with unchanged keys transferred to f31r and f39v.</p></div>'
    body+='<h2>Actual f26r: previous result and both new methods</h2><p>Lower is better. The old result had 4,096 evaluations; each new method has 8,192. Only cold versus initialized is an equal-budget comparison. All use the same two-table model and final penalized objective.</p>'
    body+=table(['Seed','Previous 4,096','Cold 8,192','Initialized 8,192','Cold word hits ≥4','Initialized word hits ≥4'],
        [[a['seed'],fmt(prior[a['previous_run_id']]['selected_loss']),fmt(a['selected_loss']),fmt(b['selected_loss']),
          a['word_hits']['pliny']['matched_tokens'],b['word_hits']['pliny']['matched_tokens']] for a,b in originals])
    body+='<h2>Does improvement transfer without changing the key?</h2><p>Independent Pliny character cost; lower is better. The methods have identical unknown positions. Whole words containing unknowns are excluded and context resets at gaps, so these are partial-coverage scores, not full-page scores.</p>'
    body+=table(['Page','Seed','Previous','Cold','Initialized','Covered symbols','Scored characters'],
        [[page,a['seed'],fmt(prior[a['previous_run_id']]['transfer'][page]['metrics']['pliny']['bits_per_character']),
          fmt(a['transfer'][page]['metrics']['pliny']['bits_per_character']),fmt(b['transfer'][page]['metrics']['pliny']['bits_per_character']),
          pct(b['transfer'][page]['code_token_coverage']),b['transfer'][page]['metrics']['pliny']['scored_characters']]
         for page in ('f31r','f39v') for a,b in originals])
    body+='<h2>Matched controls receive exactly the same procedure</h2><p>Whole-line shuffles preserve internal line structure and words while disturbing the proposed alternating clock. Symbol shuffle preserves symbol counts and space/line slots. Positive advantage means initialization improves the fitted objective relative to cold search. These controls and two seeds are not independent significance trials.</p>'
    body+=table(['Seed','Input','Cold loss','Initialized loss','Initialization advantage','Cold word hits','Initialized word hits'],
        [[a['seed'],a['control'],fmt(a['selected_loss']),fmt(b['selected_loss']),fmt(a['selected_loss']-b['selected_loss']),
          a['word_hits']['pliny']['matched_tokens'],b['word_hits']['pliny']['matched_tokens']] for a,b in manuscript])
    body+='<h2>Do the same proposed word mappings recur across seeds?</h2><p>A match here requires the same line phase, cipher word and proposed Latin word under both seeds. Repeated occurrences of one mapping are counted once. Even this agreement can arise from the language prior; controls show how often it occurs in this screen.</p>'
    display=lambda s: ''.join({'\ue000':'cth','\ue001':'ckh','\ue002':'cph','\ue003':'cfh','\ue004':'ch','\ue005':'sh'}.get(c,c) for c in s)
    body+=table(['Method','Input','Shared proposed mappings'],[[r['variant'],r['control'],
        '; '.join(f'phase {p}: {display(c)} → {w}' for p,c,w in r['shared_links']) or 'None'] for r in stable])
    body+='<h2>Known-text calibration — these are synthetic ciphertexts</h2><p>Four 600-character Latin passages/key cases: two previously used cases and two new passages at different offsets. No truth or oracle mapping is used for initialization. True-key audits occur only after both methods select their outputs. These tests measure solver capability, not manuscript decryption.</p>'
    body+=table(['Seed','Passage status','Cold recovery','Initialized recovery','Cold loss','Initialized loss','True-key loss'],
        [[a['seed'],'previous' if a['seed'] in (7,19) else 'new',pct(a['calibration']['recovery']['nonspace_edit_accuracy']),
          pct(b['calibration']['recovery']['nonspace_edit_accuracy']),fmt(a['selected_loss']),fmt(b['selected_loss']),
          fmt(a['calibration']['oracle_loss'])] for a,b in synthetic])
    body+='<h2>Actual manuscript candidate outputs</h2><p>Every original-page output from both new methods is available below. All selected control outputs and initial stage winners are retained in the evidence export.</p>'
    for pair in originals:
        for r in pair:
            body+='<details><summary>'+escape(f"{r['variant']} · seed {r['seed']}")+'</summary><h3>f26r — fitted</h3><pre>'+escape(r['plaintext'])+'</pre><p>Pliny lexicon hits ≥4 letters: '+escape(', '.join(r['word_hits']['pliny']['distinct_hits']) or 'None')+'</p>'
            for p,t in r['transfer'].items():body+='<h3>'+escape(p)+' — frozen</h3><pre>'+escape(t['plaintext'])+'</pre>'
            body+='</details>'
    body+='<h2>Execution and limits</h2><p>56 registered runs, 229,376 evaluations. Each initialized pipeline uses 2,048 evaluations per phase, then 4,096 joint evaluations. The cold pipeline uses 8,192 joint evaluations. Candidate counts match; runtime and scored-character counts need not match because phase inputs are shorter. The phase objective resets language-model history per line; joint refinement returns to the original full-text objective. Initial combinations and all stage IDs are recorded.</p><p>Preserved word spaces, compound EVA and the alternating line clock are still assumptions. Only Latin medical models are used. Previously inspected pages are not untouched holdouts. Three line permutations and two manuscript seeds do not establish significance. Repeated synthetic success without manuscript evidence is a reason to reconsider glyph units, spacing, language and historical mechanisms, not proof that more search will solve this family.</p><p><a href="README.md">Executive findings and next decision</a> · <a href="evidence.json">Full evidence</a></p>'
    html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Voynich phase initialization</title><style>body{font:17px/1.55 system-ui,sans-serif;max-width:1200px;margin:40px auto;padding:0 22px;color:#203040;background:#f7f9fb}h1{font-size:2.2rem}h2{margin-top:2.4rem}.summary{background:#e7eff8;border-left:5px solid #346b98;padding:8px 22px}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;background:white}th,td{padding:9px;border-bottom:1px solid #dce2e8;text-align:left;white-space:nowrap}th{background:#e7edf3}details{background:white;margin:12px 0;padding:14px;border:1px solid #dce2e8}summary{cursor:pointer;font-weight:650}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.7 ui-monospace,monospace}a{color:#246391}</style>'+body+'</html>'
    output.mkdir(parents=True,exist_ok=True)
    path=output/'evidence.json'
    if path.exists():
        if read_json(path)!=evidence:raise ValueError('choose a new directory for different evidence')
    else:write_json(path,evidence)
    write_json(output/'comparisons.json',{'paired':comparisons,'stable_word_links':stable,
        'mean_synthetic_recovery':{v:mean(r['calibration']['recovery']['nonspace_edit_accuracy'] for r in evidence['rows'] if r['case']=='synthetic' and r['variant']==v)
                                   for v in ('cold','separate-then-joint')}},replace=True)
    (output/'report.html').write_text(html)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();build(read_json(args.input),read_json(args.previous),args.output)
