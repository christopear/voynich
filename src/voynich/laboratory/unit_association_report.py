"""Render research findings from stored evidence; runs no experiments."""
import argparse
from html import escape
import json
from pathlib import Path

from voynich.paths import ROOT


class Report:
    def __init__(self, title):
        self.md = ['# '+title]; self.html = ['<h1>'+escape(title)+'</h1>']

    def p(self, text):
        self.md.append(text); self.html.append('<p>'+escape(text)+'</p>')

    def h(self, text):
        self.md.append('## '+text); self.html.append('<h2>'+escape(text)+'</h2>')

    def table(self, headers, rows):
        self.md.append('\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |']+
                                 ['| '+' | '.join(map(str,row))+' |' for row in rows]))
        self.html.append('<div class="scroll"><table><thead><tr>'+''.join('<th>'+escape(h)+'</th>' for h in headers)+
            '</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+
            '</tbody></table></div>')

    def link(self, label, href):
        self.md.append(f'[{label}]({href})'); self.html.append(f'<p><a href="{escape(href)}">{escape(label)}</a></p>')

    def save(self, folder):
        folder.mkdir(parents=True, exist_ok=True)
        style='body{font:17px/1.6 system-ui,sans-serif;background:#f4f3ef;color:#192e38;margin:0}main{max-width:1060px;margin:35px auto;padding:36px;background:white;border-radius:12px}h1{font-size:36px;line-height:1.2}h2{margin-top:36px;color:#215263}p{max-width:90ch}.scroll{overflow:auto}table{border-collapse:collapse;font-size:14px;width:100%}th,td{padding:10px;text-align:left;border-bottom:1px solid #dce3e5}th{background:#e8f0f2}a{color:#076579}@media(max-width:650px){main{padding:20px;margin:0}h1{font-size:28px}}'
        (folder/'README.md').write_text('\n\n'.join(self.md)+'\n')
        (folder/'report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Voynich: unit size and parser audit</title><style>'+style+'</style><main>'+''.join(self.html)+'</main></html>')


def read(folder, filename='evidence.json'):
    return json.loads((folder/filename).read_text())


def render(root):
    unit=root/'results/unit_association_2026-10-09'
    retention=root/'results/parser_retention_2026-10-09'
    audit=root/'results/unit_association_pooling_audit_2026-10-09'
    rows=read(unit)['results']; cases=read(retention)['cases']; pooling=read(audit)
    fmt=lambda x:f'{x:.3f}'
    pct=lambda x:f'{x:.1%}'
    def span(rr, key='all_section'):
        values=[r['metrics'][key]['excess'] for r in rr]
        return f'{min(values):.3f}–{max(values):.3f}'
    report=Report('Voynich: what the new round changes')
    report.p('9 October 2026. We have no supported plaintext reading. This round improves which hypotheses we can test: the synthetic parser bug is resolved for all eight fixtures, page-associated vocabulary survives stronger manuscript controls, and a vocabulary-pooling artifact is demonstrated and isolated.')
    report.table(['Question','Result','Meaning'],[
        ['Did the parser fix work?','Correct parsing rule selected in 8/8 synthetic cases','Yes for parser selection; blind plaintext recovery is still only 28.5–75.0%.'],
        ['Does Voynich retain page association?','0.115 bits above within-section permutation baseline','Yes in this bounded sample; 0.092 after layout-role conditioning. This is not proof of semantic topics.'],
        ['Which units look most promising?','Whole-word profiles sometimes overlap; letters and small mixed dictionaries fall short','Prioritise word/content-unit models, while retaining source dependence and joint fingerprint mismatches.'],
        ['Can we use the old top-200 statistic as a bound?','No: tied rare types selected by page order create spurious association','The all-type primary result survives. Historical pooled comparisons need an audit, not automatic reversal.'],
        ['Did we decrypt zodiac labels?','No; 299 labels inventoried and a falsifiable test scoped','Images and lexical anchors must be aligned independently before a semantic search.']])
    report.h('The actual manuscript result')
    report.p('16 distinct Currier B folios: eight herbal and eight biological pages, first 64 clean tokens per page (1,024 total). Split and joined doubtful-space arms retain original line and paragraph roles. The numbers below are mutual information minus a matched permutation mean, measured in bits per apparent token. They are descriptive fingerprints, not probabilities of being correct, population information ceilings or percentages decrypted.')
    report.table(['Panel','Within section','Section + layout roles','8-token block null','Type/token ratio'],[
        [r['id'],fmt(r['metrics']['all_section']['excess']),fmt(r['metrics']['all_roles']['excess']),
         fmt(r['metrics']['all_section_blocks8']['excess']),fmt(r['metrics']['shape']['ttr'])] for r in rows[:8]])
    report.p('The herbal and biological subsets, measured separately, each give about 0.116 bits of excess within-section association. Joining doubtful spaces preserves the signal. Whole-word controls preserve vocabulary but disperse its page assignments within section/roles; glyph controls preserve each page’s glyph counts and word lengths. These controls reduce association substantially. Thus page glyph composition alone does not reproduce the observed recurrent-word association in these controls.')
    report.p('Monte Carlo standard error of the split-arm null mean is 0.0011 bits (199 permutations); the corresponding null SD is 0.0156. This is uncertainty in the computed null mean, not a confidence interval for the manuscript population. Block controls retain short local runs; they do not condition on line roles. No family-rejection p-value is claimed.')
    report.h('What source-unit comparisons tell us')
    report.p('The next table shows ranges across three passage/layout seeds within each source, not confidence intervals or independent replications. Each unit becomes one apparent output word. The references match output-token count, so letters and words span different amounts of plaintext. Natural medical chapters and culinary headings are compared with artificial 256-word literary blocks. Mixed dictionaries come from a separate source partition and choose the 50 or 200 most frequent words; other words emit individual letters.')
    headers=['Unit','Celsus','Pliny','Italian recipes','Alfonsi','Dante']
    sources=('celsus','pliny','cucina','alfonsi','dante')
    kinds=('letter','pair','syllable','word','mixed50','mixed200')
    report.table(headers,[[kind]+[span([r for r in rows if r.get('source')==source and r['kind']==kind]) for source in sources] for kind in kinds])
    report.p('Reference point: Voynich split = 0.115 bits, joined = 0.124. Letters reach at most 0.020, pairs 0.084, heuristic syllables 0.101, and frequency-selected mixed codes 0.055. These are observed profile gaps, not universal bounds. Whole-word Italian recipe and Alfonsi profiles straddle the manuscript value. Source choice matters: ancient medical word profiles are lower in these passages. Recipe text therefore changes the priority picture, but does not establish a medical plaintext or an Italian language identification.')
    report.p('A fixed bijective word code preserves token equality and raw empirical page MI exactly. We do not have to guess codeword spellings to assess that invariant. But an unrestricted codebook is not automatically recoverable, and a finite-sample permutation correction is not a bound on all stochastic encoders. Homophones, contextual coding, different token boundaries and changing tables were not exhaustively simulated here. A letter substitution retaining complete plaintext words belongs to the whole-word token comparison, not the one-letter/one-token arm.')
    report.h('The apparent overlaps do not solve the joint problem')
    report.table(['Whole-word source','Within section','Section + roles','Type/token range','Top-ten share range'],[
        [source,span(rr),span(rr,'all_roles'),f"{min(r['metrics']['shape']['ttr'] for r in rr):.3f}–{max(r['metrics']['shape']['ttr'] for r in rr):.3f}",
         f"{min(r['metrics']['shape']['top10_share'] for r in rr):.3f}–{max(r['metrics']['shape']['top10_share'] for r in rr):.3f}"]
        for source in sources for rr in [[r for r in rows if r.get('source')==source and r['kind']=='word']]])
    report.p('Voynich split has type/token ratio 0.474 and top-ten share 0.186. Recipe whole-word profiles have fewer types (0.377–0.399); Alfonsi has more (0.658–0.673). Role-conditioned recipe association tops out at 0.070 versus Voynich’s 0.092. Assigning plaintext units to matching layout slots preserves margins but does not create a historically realistic layout-generating process. No source/model is declared jointly compatible by an uncalibrated checklist. Syllable segmentation is heuristic, and the narrow mixed arm does not test a dictionary of specifically medicinal content words.')
    report.h('A measurement artifact found by the controls — post hoc')
    report.p('Frequency ties in the top-200 vocabulary were broken by first occurrence. Because input is grouped by page, the chosen rare types disproportionately come from early pages. Keeping that chosen vocabulary fixed during shuffling leaves the selection bias unaccounted for. A panel of entirely unique tokens gives 0.205 excess bits through this shortcut despite zero all-type excess. Identity-hash tie-breaking reduces that example to 0.00008–0.00136 bits.')
    report.table(['Panel','Original top-200 excess','Position-independent ties, range'],[
        [r['id'],fmt(r['first_occurrence']['excess']),f"{min(x['section']['excess'] for x in r['page_blind_ties']):.3f}–{max(x['section']['excess'] for x in r['page_blind_ties']):.3f}"] for r in pooling['results']])
    report.p('The all-type primary comparison did not use pooling and is unchanged. Voynich still has association with position-independent ties. The older cipher-family fingerprint uses the same first-occurrence operation, but its 5,000-token windows and frequency cutoffs differ: this diagnostic has not measured the effect on every historical verdict. Historical numerical reports are preserved; pooled evidence must be audited before serving as a binding rejection reason.')
    report.link('Post hoc diagnostic protocol','../../docs/protocols/UNIT_POOLING_AUDIT_2026-10-09.md')
    report.h('Synthetic calibration: what improved and what did not')
    report.p('All 177 admissible parsing policies were searched at the unchanged 4,096-evaluation beam budget each. Thirty-two searches were reused only after exact compatibility checks; 145 missing searches added 593,920 evaluations. Total represented budget is 724,992 evaluations. This is exhaustive over this parsing grid, not over substitution keys or all grouped ciphers.')
    report.table(['Fixture','Earlier recovery','All-survivor recovery','True parser selected','90% gate'],[
        [r['case_id'],pct(r['previous_recovery']['nonspace_edit_accuracy']),pct(r['selected_recovery']['nonspace_edit_accuracy']),
         'yes' if r['selected_true_policy'] else 'no','pass' if r['gate_pass'] else 'fail'] for r in cases])
    report.p('All eight winners now use the true parser, so their selected recovery equals recovery within the true-parser branch. The correct known key also has a better score than each returned solution. The evidence isolates a remaining optimisation shortfall under the fixed budget; it does not prove the scorer has the correct global optimum. Known-key round trips are exact, but the blind key search still fails all eight 90% gates. No additional original-page key search or transfer was performed, and the earlier f26r structural infeasibility result is unchanged.')
    report.p('Verification: all 177 database records and execution bindings checked; all 531 retained candidates replay exactly; all 64 synthetic spans independently decode through the trie decoder with the known keys. No evaluator exceptions. The calibration protocol was committed at 77b6819 before execution.')
    report.link('Parser calibration evidence and verification','../parser_retention_2026-10-09/README.md')
    report.h('What I recommend reviewing before the next search')
    report.p('Prioritise a fixed word/content-unit hypothesis and image-linked predictions, rather than another increase in letter-key search budget. First align recurring labels to drawings and test their observable referents without forcing them to be zodiac sign names. Then, if defensible anchors exist, compare whole-word and bounded compositional codebooks with reserved lexical types and folios. A free codebook cannot decode unseen entries from a handful of cribs.')
    report.link('Crib scope: assumptions, alternate referents and stopping rules','../../docs/protocols/CRIB_SCOPE_2026-10-09.md')
    report.p('The zodiac inventory contains 299 labels, 271 clean under the current parser, and 22 whole-label spellings recurring across panels. This is not a plaintext dictionary. The label panels are a different domain from the Currier B paragraph sample. No semantic assignments have been fitted, and the needed image/label alignments remain unverified at glyph level.')
    report.h('Reproduction and limitations')
    report.p('Software validation: all 208 tests passed, including PostgreSQL integration against the separate voynich_test database. Source distribution and wheel builds passed; the CLI discovers stages 01–27. The rendered report was visually checked.')
    report.p('The unit protocol and implementation were committed at 7f40ea6 before execution. Estimator gates passed: 50 IID panels averaged −0.0021 excess bits; 10 planted page-vocabulary panels averaged 0.3491. All 90 reference panels, both manuscript arms and six controls ran as declared. The pooling audit is explicitly post hoc, declared at 99780ae before its diagnostic execution. No manuscript cipher readings or statistical family exclusions are claimed.')
    report.p('Only ZL3b was measured in this stage; joining doubtful spaces is not cross-transcription replication. Sections are observational, not proven topics. Normalised modern editions differ from medieval spelling, abbreviation and manuscripts. Source chapters and arbitrary literary blocks differ from page breaks. The small 64-token pages are noisy; seeds are sensitivity draws, not independent corpora. Matched layout margins do not model plaintext/layout dependence. Population data-processing bounds remain conditional on a fixed page-independent aligned channel.')
    report.link('Frozen unit study protocol','../../docs/protocols/UNIT_ASSOCIATION_2026-10-09.md')
    report.link('Raw numerical evidence','evidence.json')
    report.link('Source hashes and execution manifest','manifest.json')
    report.link('Source provenance, editions and licences','../../data/unit_association_sources/README.md')
    report.p('Run in a full checkout copy, using a NEW output path: uv run --locked python -m voynich.experiments.e27_unit_association --output results/<new-dir>. Historical directories must not be overwritten. Post hoc audit: python -m voynich.experiments.posthoc_e27_pooling --source results/<new-dir> --output results/<new-audit-dir>. Prepared source chapters, exact manuscript slots, selected chapter IDs and offsets are exported for inspection.')
    report.save(unit)
    brief=Report('All-survivor synthetic parser calibration')
    brief.p('The correct parser is retained AND blindly selected in 8/8 cases. Plaintext recovery improves to 28.5–75.0%, but remains below the frozen 90% gate in every case. This repairs a pruning failure without certifying the substitution-key solver. No new manuscript key search occurred.')
    brief.table(['Case','Earlier nonspace accuracy','New nonspace accuracy','Oracle loss','Returned loss'],[
        [r['case_id'],pct(r['previous_recovery']['nonspace_edit_accuracy']),pct(r['selected_recovery']['nonspace_edit_accuracy']),fmt(r['oracle_loss']),fmt(r['selected']['top'][0]['loss'])] for r in cases])
    brief.p('177 policies, 32 reused searches, 145 new searches; 593,920 new evaluations and 724,992 represented evaluations. Beam width eight and 4,096 evaluations per policy unchanged. Keys were hidden during search; truth is used only in post-selection diagnostics. Eight cases are two texts × two spacing arms × two seeds, not eight independent sources.')
    brief.link('Verification record','verification.json');brief.link('Full operating report','../unit_association_2026-10-09/report.html')
    brief.link('Protocol','../../docs/protocols/PARSER_RETENTION_2026-10-09.md')
    brief.p('Producing module: voynich.laboratory.parser_retention. Verification: voynich.laboratory.parser_retention_verify. Reruns require PostgreSQL, the retained historical prior run IDs and a new output directory. Existing historical searches must not be overwritten. New specifications and all retained policy candidates are included here; large attempt archives remain under ignored results/runs/.')
    brief.save(retention)
    short=Report('Post hoc audit: page-order tie selection')
    short.p('This diagnostic was motivated by the frozen glyph-shuffle controls, not independently preregistered evidence for a cipher family. Frequency-tied rare types selected by first occurrence can manufacture page association. Position-independent hash ties remove the demonstrated artifact; the unpooled manuscript result survives.')
    short.link('Full results and interpretation','../unit_association_2026-10-09/README.md')
    short.link('Diagnostic rules','../../docs/protocols/UNIT_POOLING_AUDIT_2026-10-09.md')
    short.p('Producer: python -m voynich.experiments.posthoc_e27_pooling --source results/unit_association_2026-10-09 --output results/<new-audit-dir>. Raw evidence contains all three tie seeds, section and role-conditioned measurements, and the unique-token diagnostic. Historical analyses have not been rerun.')
    short.save(audit)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    render(parser.parse_args().root)
