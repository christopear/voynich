"""Render the completed word-code screen and accompanying audit without new fitting."""
import argparse
import json
from pathlib import Path
import numpy as np
from voynich.paths import ROOT
from voynich.experiments.e28_word_homophones import GRID, vector
from voynich.laboratory.unit_association_report import Report


def render(root):
    folder=root/'results/word_homophones_2026-10-09';audit=root/'results/historical_pooling_audit_2026-10-09'
    e=json.loads((folder/'evidence.json').read_text());a=json.loads((audit/'evidence.json').read_text())
    fmt=lambda x:f'{x:.3f}'
    label=lambda index:' / '.join(f'{v:.0%}' for v in GRID[index])
    r=Report('Word-code alternatives: a useful constraint, no decipherment')
    r.p('9 October 2026. The suggested recipe-word experiment is complete. Independent random alternatives improve vocabulary size and common-word share, but none of the seven tested settings matches those properties AND page association together on the original manuscript panel. Meanwhile, page association replicates in IT2a and on 16 additional folios. The earlier cipher-family verdicts also survive the pooling audit.')
    r.table(['Question','Finding','Consequence'],[
        ['Can two spellings per recipe word fix the mismatch?','They bring the vocabulary measures closer, but measured page association falls short','Simple IID alternatives are not sufficient for these sources/passages. Word codes in general remain open.'],
        ['Does the manuscript signal replicate?','Yes: original ZL 0.115 bits vs IT 0.123; additional pages ZL 0.104 vs IT 0.097','The signal is not peculiar to one transcription or the original folio set.'],
        ['Did pooling invalidate the old grid verdicts?','No: every ZL configuration/window cell still fails unchanged shape metrics or audited page MI','The scoped audit warning can be cleared for the original ZL verdicts.'],
        ['Can the proposed crib validation proceed?','Only four label types cross the frozen folio split; minimum was five','Prepare alignment candidates, but do not lower the semantic-test gate after inspecting the count.']])
    r.h('What was tested')
    r.p('Three sources: Italian culinary recipes, Celsus and Pliny. Each source word has one, two or three disjoint opaque codewords. Choices are independent of page, layout and earlier choices, using the seven probability vectors below. One source word produces one apparent ciphertext word; codeword glyph structure is not modelled. Separate chapter halves supply development and validation passages. Two passage seeds per half and six encoding draws give 504 panels of 1,024 tokens. No cipher keys were searched, and no Voynich words were assigned meanings.')
    r.p('The protocol and producing code were committed at 55c7a8f before execution. All 14 independently generated positive-control targets passed the declared neighbourhood calibration. Some different probability settings are indistinguishable on these fingerprints: passing calibration does not identify the number of historical homophones.')
    r.h('The trade-off in the recipe model')
    original=e['targets']['ZL_original']
    rows=[['Voynich original',*map(fmt,vector(original))]]
    for i in range(7):
        rr=[vector(x['metrics']) for x in e['records'] if x['source']=='cucina' and x['split']=='development' and x['configuration']==i]
        rows.append([label(i),*map(fmt,np.median(rr,axis=0))])
    r.table(['Alternative probabilities','Types / tokens','Top-ten share','Page association','After layout roles'],rows)
    r.p('Two equally likely alternatives give a type/token ratio of 0.463 (Voynich 0.474) and top-ten share 0.207 (Voynich 0.186). But page-association excess is only 0.031 (Voynich 0.115), falling to 0.006 after conditioning on line/paragraph roles (Voynich 0.092). Three alternatives can also improve the first two quantities without repairing the latter two. These are medians over two passages and six draws, not independently replicated manuscripts.')
    r.p('This is not a statement that random homophones destroy underlying information. With disjoint codes, the source word U is a deterministic function of the code C. With page-independent choices, data processing in both directions gives I(C;page)=I(U;page) in the population. The permutation-excess statistic changes because independent choices split repeated observations across rarer types. The experiment tests finite-sample recurrence fingerprints, not a violation of that identity.')
    r.h('Joint selection and prospective transfer')
    r.p('The four screening scales were fixed at 0.05 for type/token ratio, 0.04 for top-ten share, and 0.05 bits each for section and role-conditioned excess MI. A joint hit requires every absolute difference to fit its scale. These are descriptive neighbourhoods, not calibrated rejection thresholds. One setting per source was selected on the original ZL target from median development fingerprints, then frozen for all other comparisons. No setting was reselected on IT2a or additional pages.')
    r.table(['Source','Selected probabilities','Development max-scaled distance','Original ZL hits / 12','Additional ZL hits / 12','Additional IT hits / 12'],[
        [name,label(c['selected']['configuration']),fmt(c['selected']['distance']),
         c['tests']['ZL_original']['joint_hits'],c['tests']['ZL_additional']['joint_hits'],c['tests']['IT_additional']['joint_hits']]
         for name,c in e['comparisons'].items()])
    r.p('No development draw from any source/configuration is a joint hit. The selected recipe setting is 90/10, but its median distance is 1.514, outside the neighbourhood, and it has zero hits on original ZL, joined-space ZL, IT or additional-page targets. This is a no-joint-match result for this bounded screen, not a statistical exclusion of word coding.')
    r.p('Celsus without alternatives falls inside the additional-ZL neighbourhood for one of two validation passages (six identical encoding-seed records), but fails the original panel and additional IT. This is one passage, not six independent successes. The broader lesson is source and section dependence: we cannot identify a recipe/medical plaintext genre from the earlier overlap. The chapter-disjoint design changed the recipe passages relative to stage 27; the baseline profile is consequently different and source sampling remains important.')
    r.h('Actual manuscript replication')
    r.table(['Panel','Types / tokens','Top-ten share','Page association','After layout roles'],[
        [name,*map(fmt,vector(m))] for name,m in e['targets'].items()])
    r.p('Original panel: 16 distinct herbal/biological folios. Additional panel: eight different herbal folios and eight starred-text folios; there are not enough remaining biological folios for a second matching set of eight. Thus the additional panel tests a new section mix, not an identical population. Each panel uses 64 clean tokens per page. IT2a uses the same pages, but not exact token/glyph alignment; it is a sensitivity analysis of the same manuscript, not another manuscript.')
    r.p('Within-section excess association is 0.115/0.123 in original ZL/IT and 0.104/0.097 on additional ZL/IT. Role-conditioned values are 0.092/0.094 and 0.080/0.077 respectively. Page-associated vocabulary remains a robust target for future models; it still does not establish semantic topic, cipher status or a plaintext reading.')
    r.h('The historical pooling audit is closed for the ZL verdicts')
    r.table(['Window','Original first-occurrence pool','Position-independent lexical ties','No vocabulary cap','Every original grid cell remains negative'],[
        [w,fmt(v['target']['first']),fmt(v['target']['identity']),fmt(v['target']['all']),str(all(v['all_cells_excluded'].values()))]
        for w,v in a['windows'].items()])
    r.p('Audit coverage: 228 configuration cells per window, 456 in total. Of these, 434 already fail P1–P4, which pooling cannot affect. The remaining 22 cells were resimulated at all six original seeds: 132 runs. Their original page-MI values and the original target/bootstrap values reproduced exactly. With freshly recomputed target bootstrap SDs, every remaining cell fails page MI under both position-independent ties and no cap. This proves the old ZL conjunction verdicts unchanged without needing all other capped fingerprints to be unchanged.')
    r.p('This independently supports Claude’s overall audit conclusion, but is not a replication of all his reported decimals or the claimed maximum P5/P7–P9 shifts. Our tie rule is lexical identity, not an unspecified scratch-script rule. IT/v101 full-grid verdicts and old calibration gates were not rerun. The stage-27 small-sample pooling artifact remains real; the sufficient audit closes the specified old-ZL concern, not a general approval of first-occurrence pooling.')
    r.link('Audit protocol','../../docs/protocols/HISTORICAL_POOLING_AUDIT_2026-10-09.md')
    r.link('Audit evidence','../historical_pooling_audit_2026-10-09/evidence.json')
    r.h('Recurring labels: preparation without forced meanings')
    r.p('Only otaly, okeoly, okydy and okaram cross the proposed development folios 70–71 / reserved folios 72–73 split. The scope specified five anchor types; that gate is not met. The 22 recurring types have 53 occurrences in total. The coordinate packet keeps exact spelling candidates for each occurrence, including missing and ambiguous matches, without pretending that a cached token box is a verified illustrated referent. No fuzzy spelling equivalences, image-coordinate transformations or lexical guesses were invented.')
    r.link('Alignment review packet','../label_alignment_2026-10-09/report.html')
    r.p('Image/label correspondence remains to be verified manually. A future protocol could use additional label domains or a different justified validation design, but this round does not silently change the reserved split or its threshold. No semantic crib test was run.')
    r.h('Next discriminating hypothesis')
    r.p('Independent random alternatives alone are insufficient here. I would next compare a narrowly bounded mechanism that reuses an alternative within a page or local passage against IID choice, with the same codebook size and marginal alternative frequencies. That changes recurrence while remaining hand-executable in principle. Page-specific choice can itself create association, so it must be charged as state and tested on reserved pages; a successful fingerprint fit would still not be a reading. Content-selected medicinal word lists and genuine layout generation remain separate hypotheses, rather than additions silently piled onto this model.')
    r.p('Before semantic search, finish the label-image alignment and establish an adequately powered reserved prediction set. Do not increase letter-solver budget as a substitute. No historical key-size bound was imposed: the full-source recipe dictionaries have 1,484/2,968/4,452 codewords for one/two/three alternatives; Celsus and Pliny dictionaries are much larger. Practical codebook size, glyph-level capacity and internal word structure remain untested constraints.')
    r.h('Validation and reproduction')
    r.p('All 504 ciphertext panels replay exactly and all 516,096 word tokens round-trip with known keys. All five manuscript panels were independently recomputed; chapter/folio separation and execution input hashes verified. These are synthetic known-key checks, not percentages of Voynich decrypted. The full 211-test suite, including PostgreSQL integration, passed. Source and wheel builds and CLI discovery were checked.')
    r.link('Verification','verification.json');r.link('Frozen protocol','../../docs/protocols/WORD_HOMOPHONES_2026-10-09.md')
    r.link('All draw-level results and joint residuals','evidence.json');r.link('Execution/source hashes','manifest.json')
    r.p('Rerun in a full checkout with a new directory: uv run --locked python -m voynich.experiments.e28_word_homophones --output results/<new-dir>. Replay: python -m voynich.laboratory.word_homophone_verify --directory results/<new-dir>. Historical audit: python -m voynich.experiments.posthoc_e24_pooling_audit --output results/<new-audit-dir>. No new dependencies or manuscript key searches were needed.')
    r.save(folder)
    p=folder/'report.html';p.write_text(p.read_text().replace('<title>Voynich: unit size and parser audit</title>','<title>Voynich: word-code alternatives</title>'))
    ar=Report('Historical pooling audit: original ZL verdicts survive')
    ar.p('A sufficient audit of 456 historical configuration/window cells. 434 fail unchanged P1–P4. The remaining 22 cells, resimulated with all six original seeds, fail recomputed page MI under both position-independent ties and no vocabulary cap. Every original ZL family/window grid verdict remains negative. This is not a universal family exclusion.')
    ar.p('132 original simulations and both original target/page-bootstrap measurements reproduced exactly. New 200-resample target SDs were used. P5/P7–P9 numerical shifts, IT/v101 full grids and historical calibration gates were not rerun; no claim is made to reproduce Claude’s entire scratch audit.')
    ar.link('Full report','../word_homophones_2026-10-09/README.md');ar.link('Rules and audit scope','../../docs/protocols/HISTORICAL_POOLING_AUDIT_2026-10-09.md')
    ar.p('Producer: voynich.experiments.posthoc_e24_pooling_audit. Code and protocol committed before execution at 55c7a8f. Input hashes and source snapshot are in evidence.json. Use a new output directory for reruns; historical files were not overwritten.');ar.save(audit)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    render(p.parse_args().root)
