"""Executive report separating cipher execution, search power and model validity."""
import argparse
from collections import Counter
from pathlib import Path
from statistics import mean
import html

from voynich.laboratory.manifest import file_hash,fingerprint
from voynich.ciphers.ambiguity import count_mapping_completions
from voynich.storage.artifacts import read_json,write_json


def escape(value):
    return html.escape(str(value))


def pct(value):
    return '—' if value is None else f'{100*value:.1f}%'


def table(headers,rows):
    return '<div class="scroll"><table><thead><tr>'+''.join(f'<th>{escape(h)}</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{escape(c)}</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def compile_evidence(directory,audit):
    summary=read_json(directory/'summary.json')
    # Additional post-search audit includes near-correct results above the 95% gate.
    # Original diagnoses, gates and search outcomes remain unchanged.
    for row in summary['cases']:
        row['posthoc_objective_prefers_inexact']=(row['metrics']['nonspace_edit_accuracy']<1 and
            row['selected_loss'] is not None and row['selected_loss']<=row['oracle_loss']+1e-9)
    summary['posthoc_audit_note']='Objective preference checked for every inexact answer, including those above the predeclared 95% threshold. Original gates and diagnoses retained.'
    if summary['status']!='completed':raise ValueError('screen is not complete')
    runs=[];envs={}
    for path in sorted((directory/'runs').glob('*/summary.json')):
        result=read_json(path);manifest=read_json(path.parent/'manifest.json')
        env=manifest.pop('environment');env_id=fingerprint(env);envs[env_id]=env
        runs.append({'run_id':result['run_id'],'spec_id':result['spec_id'],'manifest':manifest,
            'environment_id':env_id,'evaluations':result['evaluations'],'failures':result['failures'],
            'best':result['top'][:1],'strategy_diagnostics':result['strategy_diagnostics'],
            'stop_reason':result['stop_reason'],'state':result['state'],'artifact_dir':str(path.parent),
            'summary_sha256':file_hash(path)})
    fixture_cache={}
    by_id={run['run_id']:run for run in runs}
    for row in summary['cases']:
        fixture_path=directory/'private-fixtures'/f"{row['case']}.json"
        if fixture_path.exists():
            fixture=fixture_cache.setdefault(row['case'],read_json(fixture_path))
            tokens=[fixture['ciphertext'][a:b] for _,_,a,b in fixture['alignment'] if fixture['ciphertext'][a:b]!=' ']
            row['posthoc_fixture_composition']={
                'full_code_lengths':dict(Counter(str(len(c)) for c in fixture['key'])),
                'active_code_lengths':dict(Counter(str(len(c)) for c in set(tokens))),
                'two_character_token_fraction':sum(len(c)==2 for c in tokens)/max(1,len(tokens))}
        winners=by_id[row['run_ids']['positive']]['best']
        if winners:
            components=dict(winners[0]['score']['components'])
            truth_components=dict(row['oracle_score']['components'])
            if (row.get('frozen') or {}).get('valid_segmentation') and row.get('assumptions'):
                row['posthoc_unseen_mapping_completions']=count_mapping_completions(
                    winners[0]['candidate']['key'],tuple(row['assumptions']['units']),
                    row['assumptions']['capacity'],len(row['frozen']['unknown_codes']))
            row['posthoc_cost_gap_bits']={name:components.get(name,0)-value for name,value in truth_components.items()}
            row['posthoc_plaintext_length_ratio']=len(row['examples']['recovered'].replace(' ',''))/max(1,len(row['examples']['truth'].replace(' ','')))
    expected={rid for row in summary['cases'] for rid in row['run_ids'].values()}
    if {r['run_id'] for r in runs}!=expected or len(runs)!=len(expected):
        raise ValueError('missing or duplicate registered runs')
    if sum(r['evaluations'] for r in runs)!=summary['total_evaluations']:
        raise ValueError('evaluation totals do not reconcile')
    return {'schema':1,'study':summary,'runs':runs,'environments':envs,'prior_oracle_audit':read_json(audit),
        'summary_sha256':file_hash(directory/'summary.json'),'prior_audit_sha256':file_hash(audit),
        'evaluator_exceptions':sum(r['failures'] for r in runs),
        'interpretation':'Synthetic, independent-author medical calibration. No Voynich search, no family exclusion.'}


def build_report(evidence,output):
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/'evidence.json',evidence)
    study=evidence['study'];rows=study['cases'];prior=evidence['prior_oracle_audit']['cases']
    aggregate=[]
    for family in study['plan']['families']:
        for algorithm in study['plan']['algorithms']:
            chosen=[r for r in rows if r['family']==family and r['algorithm']==algorithm]
            if not chosen:continue
            aggregate.append([family,algorithm,len(chosen),pct(mean(r['metrics']['nonspace_edit_accuracy'] for r in chosen)),
                sum(r['metrics']['nonspace_edit_accuracy']>=.95 for r in chosen),
                sum(r['screening_gate'] for r in chosen),
                sum(r['diagnosis']=='search-gap-demonstrated' for r in chosen),
                sum(r.get('posthoc_objective_prefers_inexact',False) for r in chosen)])
    diagnostics=Counter(r['diagnosis'] for r in rows)
    exact=sum(r['metrics']['nonspace_edit_accuracy']==1 for r in rows)
    gates=sum(r['screening_gate'] for r in rows)
    narrative_better=sum(r['truth_nll_narrative_per_character']<r['truth_nll_medical_per_character'] for r in rows)
    prior_counts=Counter(r['diagnosis'] for r in prior)
    failures=sum(r.get('posthoc_objective_prefers_inexact',False) for r in rows)
    if failures:
        recommendation=f'Fix the objective before scaling the affected families: {failures} selected wrong answers score at least as well as their true keys, including any near-correct results above the 95% recovery threshold. More search alone cannot reliably deliver exact recovery in those cases.'
    else:
        recommendation='The next decision is how to improve search on the unresolved families, then repeat on a larger independent-source panel. The absence of a found objective failure does not validate the objective globally.'
    examples=[]
    for row in rows:
        ex=row['examples'];frozen=row['frozen'] or {}
        examples.append('<details><summary>'+escape(row['case']+' / '+row['algorithm'])+' — '+pct(row['metrics']['nonspace_edit_accuracy'])+' development</summary>'+
            '<p><strong>Diagnosis:</strong> '+escape(row['diagnosis'])+'. Boundary F1 '+pct(row['boundary_f1'])+'.</p>'+
            ''.join('<label>'+escape(label)+'</label><pre>'+escape(value)+'</pre>' for label,value in [
                ('Known synthetic source (shown only after search)',ex['truth']),('Ciphertext',ex['ciphertext']),
                ('Recovered without the key',ex['recovered']),('Reserved source',ex['frozen_truth']),
                ('Frozen-key decoding — ? means an unknown code',frozen.get('plaintext',''))])+
            '<p>Remaining assignments for unseen reserved codes, conditional on this key and segmentation: '+escape(row.get('posthoc_unseen_mapping_completions','not assessed'))+'. No completion was selected or scored.</p>'+
            '<p>Positive run: <code>'+escape(row['run_ids']['positive'])+'</code></p></details>')
    case_table=[]
    for row in rows:
        f=row['frozen'] or {}
        case_table.append([row['case'],row['algorithm'],pct(row['metrics']['nonspace_edit_accuracy']),
            pct((f.get('metrics') or {}).get('nonspace_edit_accuracy')),pct(f.get('code_token_coverage')),
            'yes' if row['beats_shuffled'] else 'no','PASS' if row['screening_gate'] else 'FAIL',
            row['diagnosis'],row['invalid_candidates']['positive']])
    oracle_table=[]
    for row in rows:
        gap=None if row['selected_loss'] is None else row['selected_loss']-row['oracle_loss']
        oracle_table.append([row['case'],row['algorithm'],f"{row['oracle_loss']:.4f}",
            '—' if row['selected_loss'] is None else f"{row['selected_loss']:.4f}",
            '—' if gap is None else f'{gap:+.4f}',pct(row['boundary_f1'])])
    paired=[]
    beam_wins=annealing_wins=ties=0
    for case in sorted({r['case'] for r in rows}):
        pair={r['algorithm']:r for r in rows if r['case']==case}
        if set(pair)!={'beam','annealing'}:continue
        delta=pair['beam']['metrics']['nonspace_edit_accuracy']-pair['annealing']['metrics']['nonspace_edit_accuracy']
        if abs(delta)<1e-12:ties+=1
        elif delta>0:beam_wins+=1
        else:annealing_wins+=1
        paired.append([case,pct(pair['annealing']['metrics']['nonspace_edit_accuracy']),pct(pair['beam']['metrics']['nonspace_edit_accuracy']),f'{100*delta:+.1f} pp'])
    body=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Medical cipher recovery — decision report</title><style>
:root{{color-scheme:light;--ink:#193433;--accent:#146a65}}*{{box-sizing:border-box}}body{{margin:0;background:#f4f2eb;color:var(--ink);font:16px/1.6 system-ui,sans-serif}}main{{max-width:1200px;margin:auto;padding:42px 28px 80px}}h1{{font-size:clamp(30px,4vw,48px);line-height:1.12;max-width:960px}}h2{{margin-top:44px;font-size:26px}}p{{max-width:1000px}}.eyebrow{{letter-spacing:.12em;font-size:12px;font-weight:700}}.callout{{background:#e1eee8;border-left:5px solid var(--accent);padding:20px 24px;margin:24px 0}}.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:12px}}.stat{{background:white;padding:18px;border-radius:8px}}.stat strong{{display:block;font-size:30px;color:var(--accent)}}.scroll{{overflow-x:auto;background:#fff;border:1px solid #d2dcd5;border-radius:8px;margin:18px 0}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:11px 12px;border-bottom:1px solid #e3e7e1;text-align:left;vertical-align:top}}th{{background:#e7ece5}}td:first-child{{font-weight:600}}details{{background:white;border:1px solid #d2dcd5;border-radius:8px;margin:10px 0;padding:14px 18px}}summary{{cursor:pointer;font-weight:650}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f5ef;padding:14px;font-size:13px;line-height:1.7}}label{{display:block;font-weight:650;margin-top:12px}}a{{color:#126c66}}code{{overflow-wrap:anywhere}}.muted{{color:#596b63;font-size:14px}}li{{margin:7px 0}}@media print{{main{{padding:0}}details{{break-inside:avoid}}}}
</style><main><div class="eyebrow">VOYNICH RESEARCH · MEDICAL CALIBRATION · 8 OCTOBER 2026</div>
<h1>Can the solver recover medical text—and what stops it when it cannot?</h1>
<p>This is a test of our tools for pursuing the hypothesis of a medicinal cipher around the fifteenth century. We encrypt known Latin medical passages, hide the key from the solver, and inspect failures after search. <strong>No Voynich text is decoded or used for fitting in this study.</strong></p>
<div class="callout"><strong>Executive decision</strong><p>The key-search beam recovered more plaintext than annealing in {beam_wins} paired cases, tied in {ties}, and recovered less in {annealing_wins}, at the same candidate budget. These are descriptive comparisons on a small panel.</p><p>{escape(recommendation)}</p><p>Simple substitution is a calibration task here, not a claim that it explains Voynich. Grouped codes and alternative spellings are the more relevant next capabilities. Preserved word spaces, a known emission inventory and restricted code lengths still make these tasks easier than the manuscript.</p></div>
<div class="stats"><div class="stat"><strong>{len(evidence['runs'])}</strong>persisted searches</div><div class="stat"><strong>{study['total_evaluations']:,}</strong>scored candidates</div><div class="stat"><strong>{exact}/{len(rows)}</strong>exact development recoveries</div><div class="stat"><strong>{gates}/{len(rows)}</strong>full screening passes</div></div>
<h2>What changed since the previous report?</h2>
<ol><li><strong>We diagnosed the old failures.</strong> {prior_counts['search-gap-demonstrated']} original glyph/homophonic cases had a true answer that scored better than the answer found. The search missed it. {prior_counts['representation-mismatch']} grouped/mixed cases had a representation mismatch, so they were unsuitable clean tests of recovery.</li>
<li><strong>We removed that grouped-code restriction.</strong> A code such as AB can now stand for a letter or pair without forcing separate A and B mappings. Every new fixture's true active key is valid under its declared evaluator and decodes exactly.</li>
<li><strong>We tested medical text across authors.</strong> Celsus is searched using a model trained on Pliny, and vice versa. Neither target author's text is in the model's training input.</li>
<li><strong>We tested a key-search beam against annealing.</strong> They use the same initial candidates, mutation rules and candidate budget. This beam retains alternative complete mappings and boundary policies; it is separate from the older decoder's segmentation beam.</li></ol>
<h2>Results by cipher family</h2>
<p>Four passage/key instances per algorithm and family. Averages describe this small panel; they are not probabilities of cracking a historical cipher. A development recovery needs at least 95% non-space accuracy. A full pass additionally needs at least 90% reserved accuracy, complete reserved-code coverage and a better score than the shuffled control.</p>
{table(['Family','Search','Cases','Mean development','≥95% development','Full passes','Search gaps','Objective prefers inexact'],aggregate)}
<h2>What the struggles mean</h2>
<ul><li><strong>Search gap:</strong> the valid true key scores better than the found wrong answer. The optimizer has demonstrated room to improve. This does not prove that every better-scoring key is correct.</li>
<li><strong>Objective failure/tie:</strong> the found wrong answer scores at least as well as the true key. Searching harder could reinforce the wrong answer; a scoring/model change needs a new independent test.</li>
<li><strong>Unknown reserved codes:</strong> the learned key cannot translate symbols/codes absent from development. Their occurrences are marked ?, counted as errors and reported separately from whole-text accuracy.</li>
<li><strong>Boundary F1:</strong> overlap between inferred and true code ends, computed after search. Variable codes require discovering both the segmentation policy and mappings.</li></ul>
{table(['Diagnosis','Case/algorithm results'],sorted(diagnostics.items()))}
<h2>Did beam search help?</h2>
<p>This compares one bounded beam design with one annealing schedule. The best objective score and the best actual decipherment need not agree. More retained alternatives do not guarantee improvement, and these results do not rule out other beam designs.</p>
{table(['Same passage/key','Annealing accuracy','Beam accuracy','Beam minus annealing'],paired)}
<h2>Reserved text and operational detail</h2>
<p>Reserved text never updates the key or segmentation policy. Coverage is the fraction of code occurrences with a learned mapping; the complete output can still be wrong. Seed 7 and seed 19 use different passages, so key difficulty and passage difficulty are confounded.</p>
{table(['Case','Search','Development','Reserved accuracy','Reserved code coverage','Beats shuffled','Full gate','Diagnosis','Invalid positive proposals'],case_table)}
<h2>Inspect actual readings</h2><p>These examples reveal the distinction between readable recovery, partial mappings and convincing-looking mistakes. Synthetic truth is displayed only for evaluation.</p>
{''.join(examples)}
<h2>Does the scoring rule prefer the true answer?</h2>
<p><strong>Additional post-search audit:</strong> the original diagnosis labels classify results at or above 95% as recovered. Here we also check whether any remaining errors in those near-correct results are preferred by the objective. This changes neither gates nor selected keys.</p>
<p>Lower loss is better. A positive gap means the known true key beats the selected key. Oracle keys never initialize or guide search. They use only codes active in development so unused entries do not inflate their costs.</p>
{table(['Case','Search','True-key loss','Selected loss','Selected minus true','Boundary F1'],oracle_table)}
<h2>Limits that matter for Voynich</h2>
<ul><li>These are ancient Latin medical/herbal texts in modern editions. We still need medieval recipe/herbal corpora and Italian medical material. Cross-author validation is stronger than the previous same-work split, but two authors are a small panel and may share phrases or source traditions.</li>
<li>Word spaces are preserved, the language is supplied, and grouped plaintext units come from a known training-derived inventory. Real manuscript spaces, glyphs, units and language are uncertain.</li>
<li>Fixed groups have known two-character width. Variable groups use the restricted rule “first symbol determines length one or two”; search permits two codes per unit although generation uses one. That comparison does not isolate segmentation alone. The generator's 34-code variable key contains 31 single-character and only three two-character codes; it is a mostly single-character construction. Actual token-length proportions are retained in the JSON.</li>
<li>Only a token-shuffled negative is used here, preserving code counts and space positions. This screening gate is weaker than the earlier three-control gate and has no calibrated false-positive rate.</li>
<li>The post-search narrative-model comparison favored Alfonsi over the medical training model in {narrative_better}/{len(rows)} case/algorithm rows (paired algorithms repeat each passage). Domain relevance is a hypothesis to measure, not an automatic improvement.</li>
<li>Neither a negative result nor a readable synthetic solution excludes or establishes a Voynich cipher family.</li></ul>
<h2>Audit and reproduction</h2>
<p>{len(evidence['runs'])} unique run IDs, {study['total_evaluations']:,} scored proposals, {evidence['evaluator_exceptions']} captured evaluator exceptions. Invalid proposals are counted separately in the table. The 16-search, 256-evaluation engineering smoke test is excluded from these totals. The earlier oracle audit evaluates existing results without rerunning their searches.</p>
<p><a href="evidence.json">Download the evidence JSON</a> for source hashes, plans, run IDs, environments, metrics and selected candidates. The execution protocol is <code>docs/protocols/MEDICAL_RECOVERY_2026-10-08.md</code>. Raw bounded run artifacts and PostgreSQL registrations remain available locally; the export does not contain every attempted decoding.</p>
<p class="muted">Source attribution: Perseus Digital Library / Trustees of Tufts University. Celsus, De Medicina, W. G. Spencer edition (1935–1938); Pliny, Naturalis Historia 20–27, K. F. T. Mayhoff edition (1906). Derived source texts and quoted examples retain CC BY-SA 4.0; pinned upstream links and hashes are in evidence.json and data/laboratory_sources. Editorial notes/headings, gaps and foreign-language spans were removed explicitly. Original accents/punctuation are not reconstructed. Engineering-only tests also cover optional 12/20-symbol cipher alphabets for the next study; no blind-recovery result in this report uses those restricted alphabets.</p></main></html>'''
    path=output/'report.html';path.write_text(body);return path


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(build_report(compile_evidence(a.input,a.audit),a.output))
