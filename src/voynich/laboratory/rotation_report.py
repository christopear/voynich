"""Report nested rotating-table fits without treating dictionary hits as truth."""
import argparse
from html import escape
from pathlib import Path
from statistics import mean

from voynich.storage.artifacts import read_json, write_json


def audit_previous(evidence):
    """Post-hoc fixed-rule lexicon audit; never feeds the search objective."""
    from voynich.decipher_search.core import LanguageModel
    from voynich.laboratory.medical_recovery import sources
    from voynich.laboratory.manifest import fingerprint, file_hash
    from voynich.laboratory.rotation_pilot import word_hits
    source=sources()['pliny'];start=int(.3*len(source['text']))
    training=source['text'][start:start+60000];lm=LanguageModel(training,4)
    rows=[{**{k:r[k] for k in ('representation','capacity','algorithm','seed','control','run_id')},
           **word_hits(r['plaintext'],lm)} for r in evidence['runs']]
    return {'scope':'Post-hoc exact Pliny training-lexicon matches, length >=4; not recovered words.',
            'previous_evidence_hash':fingerprint(evidence),'raw_source_hash':file_hash(source['path']),
            'normalized_span':[start,start+len(training)],'training_hash':fingerprint(training),
            'lexicon_hash':fingerprint(sorted(lm.words)),'rows':rows}


def comparisons(evidence):
    index={(r['case'],r['period'],r['seed'],r['control']):r for r in evidence['runs']}
    if len(index)!=len(evidence['runs']):raise ValueError('duplicate run identity')
    rows=[]
    for seed in evidence['plan']['seeds']:
        for control in evidence['plan']['controls']:
            one=index[('voynich',1,seed,control)];two=index[('voynich',2,seed,control)]
            rows.append({'seed':seed,'control':control,'one_loss':one['selected_loss'],
                'two_loss':two['selected_loss'],'two_table_advantage':one['selected_loss']-two['selected_loss'],
                'one_word_fraction':one['word_hits']['pliny']['fraction'],
                'two_word_fraction':two['word_hits']['pliny']['fraction'],
                'transfer':{p:{'one_bits':one['transfer'][p]['metrics']['pliny']['bits_per_character'],
                               'two_bits':two['transfer'][p]['metrics']['pliny']['bits_per_character'],
                               'one_coverage':one['transfer'][p]['code_token_coverage'],
                               'two_coverage':two['transfer'][p]['code_token_coverage']}
                            for p in evidence['plan']['transfer']}})
    repeats=[]
    for period in evidence['plan']['periods']:
        for control in evidence['plan']['controls']:
            selected=[index[('voynich',period,s,control)] for s in evidence['plan']['seeds']]
            common=set.intersection(*(set(r['word_hits']['pliny']['distinct_hits']) for r in selected))
            repeats.append({'period':period,'control':control,'shared_hits_across_seeds':sorted(common)})
    return {'paired':rows,'repeated_words':repeats}


def build(evidence, output, previous=None):
    summary=comparisons(evidence)
    if len(evidence['runs'])!=evidence['plan']['registered_runs'] or evidence['total_evaluations']!=evidence['plan']['registered_evaluations']:
        raise ValueError('incomplete planned study')
    output.mkdir(parents=True,exist_ok=True)
    evidence_path=output/'evidence.json'
    if evidence_path.exists():
        if read_json(evidence_path)!=evidence:
            raise ValueError('choose a new report directory for different evidence')
    else:
        write_json(evidence_path,evidence)
    write_json(output/'comparisons.json',summary,replace=True)
    if previous:write_json(output/'previous_word_audit.json',previous,replace=True)
    def table(headers, rows):
        return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+escape(str(x))+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
    fmt=lambda x:f'{x:.3f}'
    pct=lambda x:f'{x:.1%}'
    orig=[r for r in summary['paired'] if r['control']=='original']
    shuffled=[r for r in summary['paired'] if r['control'].startswith('line-shuffled')]
    exceed=sum(r['two_table_advantage']>c['two_table_advantage'] for r in orig for c in shuffled if r['seed']==c['seed'])
    syn=[r for r in evidence['runs'] if r['case']=='synthetic']
    body='<h1>Does changing the table help?</h1><p>Voynich line-rotation pilot · 9 October 2026 · f26r → f31r and f39v</p>'
    body+='<div class="summary"><p><strong>Exploratory evidence, not recovered words.</strong> Two tables may fit better simply because they have more freedom. This report compares the gain with the same extra freedom on shuffled controls.</p>'
    body+='<p>On original f26r, the penalized two-table advantage is '+escape('; '.join(f"{r['two_table_advantage']:+.3f} for seed {r['seed']}" for r in orig))+'. Positive means improvement. The direction is inconsistent across these seeds.</p>'
    body+=f'<p>{len(evidence["runs"])} runs / {evidence["total_evaluations"]:,} registered evaluations. The original-page two-table gain exceeds the matched line-shuffle gain in {exceed}/6 comparisons. These comparisons reuse two searches and three control realizations; they are not independent significance tests.</p>'
    body+='<p>Blind synthetic recovery is weaker with two tables. A failed manuscript reading therefore cannot rule out rotation. No output below has been established as plaintext.</p></div>'
    body+='<h2>Hypothesis and safeguards</h2><p>One fixed injective substitution table versus two independent tables alternating on successive paragraph-text lines. State resets to zero on each page. Compound EVA units and surviving spaces are fixed. Empty filtered lines still advance the clock. Keys are never refitted on transfer pages. This tests one specific switching rule, not arbitrary rotation, dice choices, per-word tables or homophones.</p><p>Celsus character n-grams drive beam search. The objective charges a combinatorial description length for each table. Pliny scores selected outputs and exact lexicon matches independently of selection. A lexicon hit requires at least four letters; it is not evidence that the matching word is the intended plaintext.</p>'
    body+='<h2>Can the search recover this cipher when it really is present?</h2>'
    body+=table(['Tables','Seed','Nonspace recovery','Selected loss','True-key loss','Pliny word hits'],[[r['period'],r['seed'],pct(r['calibration']['recovery']['nonspace_edit_accuracy']),fmt(r['selected_loss']),fmt(r['calibration']['oracle_loss']),pct(r['word_hits']['pliny']['fraction'])] for r in syn])
    body+='<p>The encoder uses independently generated random tables. Its known key decodes exactly. Lower true-key loss identifies remaining search failure, rather than proving the language objective rejects the correct text. Four runs on one passage do not estimate detection power; the synthetic alphabet is not matched to Voynich.</p>'
    body+='<h2>Does rotation help the manuscript more than controls?</h2><p>Positive advantage means two tables improve the penalized objective. Each row uses the same input and search budget for both periods. Controls preserve whole lines and words, or preserve symbol counts and every space/line slot. Absolute losses differ from the preceding pilot because table-description costs changed.</p>'
    body+=table(['Seed','Input','One table','Two tables','Two-table advantage','One-table word hits','Two-table word hits'],[[r['seed'],r['control'],fmt(r['one_loss']),fmt(r['two_loss']),fmt(r['two_table_advantage']),pct(r['one_word_fraction']),pct(r['two_word_fraction'])] for r in summary['paired']])
    body+='<h2>Frozen transfer under the independent Pliny model</h2><p>Lower character cost is better. Coverage counts observed phase/symbol pairs with a learned mapping. Unknown-containing words are omitted from scoring and context resets at each gap; unequal coverage can bias comparisons. No unknown mapping is filled by guessing.</p>'
    for p in evidence['plan']['transfer']:
        body+='<h3>'+escape(p)+'</h3>'
        body+=table(['Seed','Input','One-table bits/char','Two-table bits/char','One-table coverage','Two-table coverage'],[[r['seed'],r['control'],fmt(r['transfer'][p]['one_bits']),fmt(r['transfer'][p]['two_bits']),pct(r['transfer'][p]['one_coverage']),pct(r['transfer'][p]['two_coverage'])] for r in summary['paired']])
    body+='<h2>Which words recur across optimizer seeds?</h2><p>The same word appearing twice is still not necessarily the same ciphertext-to-plaintext proposal. Empty intersections are shown explicitly. Repetition can come from the language prior or repeated cipher tokens.</p>'
    body+=table(['Tables','Input','Shared Pliny lexicon hits ≥4 letters'],[[r['period'],r['control'],', '.join(r['shared_hits_across_seeds']) or 'None'] for r in summary['repeated_words']])
    if previous:
        body+='<h2>Rechecking the earlier attractive words</h2><p>Post-hoc audit of all 48 previous selected outputs against the same Pliny lexicon, with the ≥4-letter rule. Token counts are not independent trials: repeated ciphertext and repeated searches reuse evidence.</p>'
        groups=[]
        for control in ('original','symbol-shuffled','word-shuffled'):
            rows=[r for r in previous['rows'] if r['control']==control]
            groups.append([control,sum(r['matched_tokens'] for r in rows),sum(r['eligible_tokens'] for r in rows),pct(mean(r['fraction'] for r in rows))])
        body+=table(['Input','Matched tokens','Eligible tokens','Mean hit fraction'],groups)
        body+='<p>Six original-page matches are repetitions of <em>febris</em> under a single proposed mapping. This is a useful lead to test, not six independently recovered medical words.</p>'
    body+='<h2>All original-page candidates</h2><p>Full outputs are shown; no promising fragments have been selected for display. All controls and their outputs are retained in the evidence export.</p>'
    for r in evidence['runs']:
        if r['case']!='voynich' or r['control']!='original':continue
        body+=f'<details><summary>{r["period"]} table(s) · seed {r["seed"]}</summary><h3>f26r — fitted</h3><pre>'+escape(r['plaintext'])+'</pre><p>Pliny lexicon hits: '+escape(', '.join(r['word_hits']['pliny']['distinct_hits']) or 'None')+'</p>'
        for p,t in r['transfer'].items():
            body+='<h3>'+escape(p)+' — frozen</h3><pre>'+escape(t['plaintext'])+'</pre>'
        body+='<h3>Tables</h3>'
        for phase in range(r['period']):
            entries=[f'{chr(ord(c)%65536)}→{u}' for c,u in sorted(r['candidate']['key'].items()) if ord(c)//65536==phase]
            # Replace private glyph labels with the conventional EVA sequences.
            entries=' · '.join(entries)
            for i,name in enumerate(('cth','ckh','cph','cfh','ch','sh')):entries=entries.replace(chr(0xE000+i),name)
            body+=f'<p>Phase {phase}</p><pre>'+escape(entries)+'</pre>'
        body+='</details>'
    body+='<h2>Interpretation limits</h2><p>Three line permutations and two optimizer seeds are a screen, not a calibrated null distribution. The search is imperfect; description lengths are an explicit model convention, not historical probabilities. Filters omit ambiguous words but retain line timing. Corpus mismatch, transcription choices, spaces, abbreviations and untested switching rules remain open. Improvements on these previously examined pages must survive further independent predictions.</p><p><a href="README.md">Executive findings and next decision</a> · <a href="evidence.json">Full evidence</a></p>'
    html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Voynich line rotation</title><style>body{font:17px/1.55 system-ui,sans-serif;max-width:1200px;margin:40px auto;padding:0 22px;color:#203040;background:#f7f9fb}h1{font-size:2.2rem}h2{margin-top:2.4rem}.summary{background:#e7eff8;border-left:5px solid #346b98;padding:8px 22px}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;background:white}th,td{padding:9px;border-bottom:1px solid #dce2e8;text-align:left;white-space:nowrap}th{background:#e7edf3}details{background:white;margin:12px 0;padding:14px;border:1px solid #dce2e8}summary{cursor:pointer;font-weight:650}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.7 ui-monospace,monospace}a{color:#246391}</style>'+body+'</html>'
    (output/'report.html').write_text(html)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    previous=parser.add_mutually_exclusive_group()
    previous.add_argument('--previous-audit',type=Path)
    previous.add_argument('--previous-evidence',type=Path)
    args=parser.parse_args()
    audit=read_json(args.previous_audit) if args.previous_audit else audit_previous(read_json(args.previous_evidence)) if args.previous_evidence else None
    build(read_json(args.input),args.output,audit)
