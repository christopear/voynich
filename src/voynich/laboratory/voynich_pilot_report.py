"""Render all pilot outputs with matched controls, without selecting a reading."""
import argparse
from collections import Counter
from html import escape
from pathlib import Path

from voynich.laboratory.voynich_pilot import represent
from voynich.storage.artifacts import read_json, write_json


def paired_rows(evidence):
    runs = evidence['runs']
    identity = lambda r: (r['representation'], r['capacity'], r['algorithm'], r['seed'])
    index = {(identity(r), r['control']): r for r in runs}
    if len(index) != len(runs):
        raise ValueError('duplicate paired identity')
    pairs = []
    for r in runs:
        if r['control'] != 'original':
            continue
        pairs.append((r, index[(identity(r), 'symbol-shuffled')], index[(identity(r), 'word-shuffled')]))
    if len(pairs)*3 != len(runs):
        raise ValueError('incomplete controls')
    return pairs


def stability(evidence):
    results = []
    for representation in evidence['plan']['representations']:
        text, labels = represent(evidence['pages']['development']['words'], representation)
        counts = Counter(labels[c] for c in text if c != ' ')
        for capacity in evidence['plan']['capacities']:
            for algorithm in evidence['plan']['algorithms']:
                rows = [r for r in evidence['runs'] if r['control'] == 'original' and
                        (r['representation'], r['capacity'], r['algorithm']) == (representation, capacity, algorithm)]
                if len(rows) != 2:
                    raise ValueError('stability requires the planned two seeds')
                same = sum(counts[c] for c in counts if rows[0]['key'][c] == rows[1]['key'][c])
                results.append({'representation': representation, 'capacity': capacity, 'algorithm': algorithm,
                                'token_weighted_mapping_agreement': same/sum(counts.values())})
    return results


def build(evidence, output):
    pairs = paired_rows(evidence)
    if sum(r['evaluations'] for r in evidence['runs']) != evidence['total_evaluations']:
        raise ValueError('evaluation total mismatch')
    output.mkdir(parents=True, exist_ok=True)
    write_json(output/'evidence.json', evidence)
    agreement = stability(evidence)
    metric = lambda r, split, model: r[split+'_metrics'][model]['bits_per_character']
    originals = [r for r, _, _ in pairs]
    gain = [100*(1-r['selected_loss']/r['initial_best_loss']) for r in originals]
    symbol_wins = sum(r['selected_loss'] < s['selected_loss'] for r,s,w in pairs)
    word_wins = sum(r['selected_loss'] < w['selected_loss'] for r,s,w in pairs)
    word_transfer_wins = sum(metric(r,'transfer','pliny') < metric(w,'transfer','pliny') for r,s,w in pairs)
    escape_cell = lambda x: escape(str(x))
    def table(headers, rows):
        return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+escape_cell(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape_cell(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
    summary = [
        'Search makes the outputs more Latin-like; it does not establish a partial decipherment.',
        f"{len(evidence['runs'])} searches completed, {evidence['total_evaluations']:,} registered search evaluations. Original-page loss improved {min(gain):.1f}–{max(gain):.1f}% relative to the best initial state.",
        f'Original pages beat symbol-shuffled controls in {symbol_wins}/{len(pairs)} paired searches, but beat word-shuffled controls in only {word_wins}/{len(pairs)}. On frozen-page transfer under the independent Pliny model, original beats word-shuffle in {word_transfer_wins}/{len(pairs)} pairs.',
        'Symbol shuffle destroys internal word patterns; beating it shows exploitable structure, not its meaning. Word shuffle preserves those patterns and is a harder control for claims about order.',
        'Every string below is a scored candidate, not a translation. Latin-looking words can arise because the optimizer is rewarded for producing Latin-looking words.'
    ]
    body = '<h1>Voynich page-search pilot</h1><p>9 October 2026 · f26r → f31r · Latin medical working hypothesis</p>'
    body += '<div class="summary">'+''.join('<p>'+escape(x)+'</p>' for x in summary)+'</div>'
    body += f'<h2>What was actually tested</h2><p>{len(evidence["pages"]["development"]["words"])} retained words on f26r drive selection. {len(evidence["pages"]["frozen"]["words"])} retained words on f31r receive the same key without refitting. Both are Currier B herbal pages. Celsus guides search; Pliny scores selected outputs independently. Two seeds, {evidence["plan"]["budget"]:,} proposals per run, population 8. Capacity 1 means one-to-one substitution; capacity 2 permits two cipher symbols per Latin letter.</p><p>Raw EVA treats transcription letters as units. Compound EVA joins cth/ckh/cph/cfh/ch/sh. Preserved spaces and fixed mappings are strong assumptions. Ambiguous words are omitted ({len(evidence["pages"]["development"]["omitted"])} and {len(evidence["pages"]["frozen"]["omitted"])} spans respectively); omissions close gaps. These are previously studied pages, not untouched holdouts.</p>'
    body += '<h2>Matched results</h2><p>Lower loss is better. Loss includes language, key and homophone-choice costs per input symbol. Gains compare the final selected candidate with the best of eight starting states. Compare within the same representation and capacity; different unit encodings have different denominators.</p>'
    body += table(['Units','Capacity','Method','Seed','Start loss','Final loss','Symbol-shuffle loss','Word-shuffle loss'],
        [[r['representation'],r['capacity'],r['algorithm'],r['seed'],*[f'{v:.3f}' for v in (r['initial_best_loss'],r['selected_loss'],s['selected_loss'],w['selected_loss'])]] for r,s,w in pairs])
    body += '<h2>Does apparent Latin-likeness transfer?</h2><p>Character cross-entropy (bits per output character, including spaces), with key penalties removed. Pliny never steers selection. Unknown-containing words are excluded in their entirety and context resets at each gap; coverage must be read alongside the score. Word-control transfer uses its own frozen key on a separately word-shuffled f31r.</p>'
    body += table(['Units','Capacity','Method','Seed','Celsus f26r','Pliny f26r','Pliny f31r','Word-control Pliny f31r','f31r coverage','Scored chars'],
        [[r['representation'],r['capacity'],r['algorithm'],r['seed'],*[f'{v:.3f}' for v in (metric(r,'development','celsus'),metric(r,'development','pliny'),metric(r,'transfer','pliny'),metric(w,'transfer','pliny'))],f"{r['transfer']['code_token_coverage']:.1%}",r['transfer_metrics']['pliny']['scored_characters']] for r,s,w in pairs])
    body += '<h2>Ordinary medical Latin anchors</h2><p>Unsearched 600-character passages outside model training. Small contextual benchmarks, not thresholds for decipherment.</p>'
    body += table(['Actual text','Celsus bits/char','Pliny bits/char'], [[name,*[f"{anchor['metrics'][n]['bits_per_character']:.3f}" for n in ('celsus','pliny')]] for name,anchor in evidence['anchors'].items()])
    body += '<h2>Key stability across seeds</h2><p>Fraction of development symbol occurrences assigned the same letter by the two seeds. Agreement may reflect the language prior; it is not accuracy.</p>'
    body += table(['Units','Capacity','Method','Agreement'], [[r['representation'],r['capacity'],r['algorithm'],f"{r['token_weighted_mapping_agreement']:.1%}"] for r in agreement])
    body += '<h2>Retained transcription input</h2><p>Plain EVA shown before compound encoding. The evidence export records omitted tokens and their manuscript loci.</p>'
    for role, page in evidence['pages'].items():
        body += '<details><summary>'+escape(page['page']+' · '+role)+'</summary><pre>'+escape(' '.join(page['words']))+'</pre></details>'
    body += '<h2>All original-page candidate outputs</h2><p>Full retained text, not a selection of promising words. Expand any row to inspect its frozen transfer and mapping. The JSON export also contains every selected control output.</p>'
    for r in originals:
        label = f"{r['representation']} · capacity {r['capacity']} · {r['algorithm']} · seed {r['seed']}"
        body += '<details><summary>'+escape(label)+'</summary><h3>f26r — fitted</h3><pre>'+escape(r['plaintext'])+'</pre><h3>f31r — frozen</h3><pre>'+escape(r['transfer']['plaintext'])+'</pre><h3>Proposed mapping</h3><pre>'+escape(' · '.join(f'{c}→{u}' for c,u in sorted(r['key'].items())))+'</pre><p>Run '+escape(r['run_id'])+'</p></details>'
    body += '<h2>Interpretation and limits</h2><p>A bijective substitution only renames symbols: entropy, repeated-symbol patterns and word lengths cannot change. The optimizer improves how those patterns align with Latin letter sequences. Homophonic mappings can merge symbols but still leave lengths fixed. Neither experiment addresses changing tables, nulls, ligatures beyond the stated compound convention, syllables, abbreviations, or false word spaces.</p><p>Two seeds and two shuffled realizations cannot calibrate significance or exclude cipher families. A four-character language model has limited sensitivity to syntax; failing the word-order control does not prove absence of meaningful order. Celsus and Pliny share genre and language; post-selection agreement does not establish medieval vocabulary or plaintext correctness. No Italian search was performed. The pilot demonstrates optimization, not an independently verified letter, word, or translation.</p><p>Next: improve representation and scoring on synthetic text with a Voynich-sized alphabet and uncertain spaces; require a candidate advantage over word-preserving controls plus stable frozen-page predictions before proposing readings.</p><p><a href="evidence.json">Full evidence export</a></p>'
    html = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Voynich page-search pilot</title><style>body{font:17px/1.55 system-ui,sans-serif;max-width:1200px;margin:40px auto;padding:0 22px;color:#203040;background:#f7f9fb}h1{font-size:2.2rem}h2{margin-top:2.4rem}.summary{background:#e7eff8;border-left:5px solid #346b98;padding:8px 22px}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;background:white}th,td{padding:9px;border-bottom:1px solid #dce2e8;text-align:left;white-space:nowrap}th{background:#e7edf3}details{background:white;margin:12px 0;padding:14px;border:1px solid #dce2e8}summary{cursor:pointer;font-weight:650}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.7 ui-monospace,monospace}a{color:#246391}</style>'+body+'</html>'
    (output/'report.html').write_text(html)
    write_json(output/'comparisons.json', {'summary': summary, 'stability': agreement,
        'symbol_control_wins': symbol_wins, 'word_control_wins': word_wins,
        'word_control_frozen_pliny_wins': word_transfer_wins})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); build(read_json(args.input), args.output)
