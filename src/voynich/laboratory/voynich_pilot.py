"""Bounded, controlled Latin-likeness pilot; outputs are NOT decipherments."""
import argparse
from collections import Counter
from dataclasses import replace
from pathlib import Path
import random
import re

from voynich.decipher_search.core import digest, LanguageModel
from voynich.experiments.runner import ExperimentRunner
from voynich.laboratory.fixtures import PublicInput
from voynich.laboratory.manifest import DatasetRef, ExperimentSpec, environment, file_hash, fingerprint
from voynich.laboratory.medical_recovery import sources
from voynich.paths import ROOT
from voynich.search.codebooks import CodebookProblem, CodebookEvaluator, CodebookSearch, partial_transfer
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import write_json
from voynich.storage.database import make_engine
from voynich.storage.registry import Registry
from voynich.voynich_core import eva_glyphs


def clean_page(path, page):
    """Keep certain, plain EVA words; record every omitted annotated token.

    Comma denotes an uncertain separator: omit the whole comma-containing
    span rather than adjudicate it. Never turn a partial word into a full word.
    Returned offsets refer to lines of the raw file (zero based, half open).
    """
    kept, omitted, loci, offsets = [], [], [], []
    metadata = None
    for index, raw in enumerate(path.read_text().splitlines()):
        if re.match(r'^<' + re.escape(page) + r'>\s', raw):
            metadata = dict(re.findall(r'\$(\w)=([^\s>]+)', raw))
        match = re.match(r'^<(' + re.escape(page) + r'\.\d+),([^>]+)>\s*(.*)$', raw)
        if not match or 'P' not in match[2]:
            continue
        offsets.append(index); loci.append(match[1])
        body = match[3].replace('<->', '.')
        for marker in ('<%>', '<$>', '<~>'):
            body = body.replace(marker, '')
        # Protect annotation-internal spaces/dots from creating spurious words.
        annotations = {}
        def protect(match):
            label = f'@annotation{len(annotations)}@'
            annotations[label] = match[0]
            return label
        body = re.sub(r'<![^>]*>|\[[^\]]*\]|\{[^}]*\}', protect, body)
        for word in re.split(r'[.\s]+', body):
            if not word:
                continue
            if re.fullmatch('[a-z]+', word):
                kept.append(word)
            else:
                for label, original in annotations.items():
                    word = word.replace(label, original)
                omitted.append({'locus': match[1], 'token': word})
    if not kept or metadata is None:
        raise ValueError('missing page/header or no certain words')
    return {'page': page, 'metadata': metadata, 'words': kept, 'omitted': omitted,
            'loci': loci, 'raw_line_span': [min(offsets), max(offsets)+1],
            'caveat': 'Omitted words close gaps; retained adjacency and word spaces are assumptions.'}


def represent(words, representation):
    if representation == 'eva':
        return ' '.join(words), {c: c for c in sorted(set(''.join(words)))}
    if representation != 'compounds':
        raise ValueError('unknown representation')
    # Stable global labels; all six conventional EVA compounds remain distinct.
    compounds = ('cth', 'ckh', 'cph', 'cfh', 'ch', 'sh')
    labels = {c: chr(0xE000+i) for i, c in enumerate(compounds)}
    encoded = ' '.join(''.join(labels.get(c, c) for c in eva_glyphs(w)) for w in words)
    return encoded, {c: next((k for k, v in labels.items() if v == c), c)
                     for c in sorted(set(encoded)-{' '})}


def control_text(text, kind, seed):
    rng = random.Random(seed)
    if kind == 'original':
        return text
    if kind == 'symbol-shuffled':
        letters = list(text.replace(' ', '')); rng.shuffle(letters)
        return ''.join(' ' if c == ' ' else letters.pop() for c in text)
    if kind == 'word-shuffled':
        words = text.split(); rng.shuffle(words)
        return ' '.join(words)
    raise ValueError('unknown control')


def language_metrics(text, lm):
    """Score only fully covered words, resetting context at unknown words.

    Includes spaces within covered runs. Reports scored length explicitly;
    never silently deletes '?' and creates artificial letter adjacency.
    """
    runs, current = [], []
    for word in text.split():
        if '?' in word:
            if current:
                runs.append(' '.join(current)); current = []
        else:
            current.append(word)
    if current:
        runs.append(' '.join(current))
    count = sum(len(r) for r in runs)
    words = [w for w in text.split() if '?' not in w]
    return {'bits_per_character': sum(lm.nll(r) for r in runs)/count if count else None,
            'scored_characters': count, 'covered_words': len(words),
            'training_lexicon_token_fraction': sum(w in lm.words for w in words)/len(words) if words else None}


def run(output, budget=4096):
    if budget < 8:
        raise ValueError('budget must cover initial population')
    path = ROOT/'data/ZL3b-n.txt'
    dev, frozen = [clean_page(path, p) for p in ('f26r', 'f31r')]
    if any(p['metadata'].get('L') != 'B' or p['metadata'].get('I') != 'H' for p in (dev, frozen)):
        raise ValueError('pilot requires Currier B herbal pages')
    corpora = sources()
    texts = {}
    for name, s in corpora.items():
        start = int(.3*len(s['text']))
        texts[name] = s['text'][start:start+60000]
    training = texts['celsus']
    lms = {name: LanguageModel(text, 4) for name, text in texts.items()}
    plan = {'schema': 1, 'development': 'f26r', 'frozen_transfer': 'f31r',
            'training': 'celsus', 'post_selection_model': 'pliny',
            'representations': ['eva', 'compounds'], 'capacities': [1, 2],
            'algorithms': ['annealing', 'beam'], 'seeds': [7, 19],
            'controls': ['original', 'symbol-shuffled', 'word-shuffled'],
            'budget': budget, 'population': 8, 'transcription_sha256': file_hash(path),
            'scope': 'Exploratory Latin-only pilot; preserved spaces, fixed single-symbol mappings; no truth accuracy or decipherment claim.'}
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'plan.json', plan)
    write_json(output/'pages.json', {'development': dev, 'frozen': frozen})
    env = environment(ROOT); write_json(output/'environment.json', env)
    engine = make_engine(); registry = Registry(engine); rows = []
    try:
        for representation in plan['representations']:
            cipher, labels = represent(dev['words'], representation)
            held, held_labels = represent(frozen['words'], representation)
            for capacity in plan['capacities']:
                for seed in plan['seeds']:
                    for algorithm in plan['algorithms']:
                        for control in plan['controls']:
                            text = control_text(cipher, control, seed+1000)
                            target = control_text(held, control, seed+2000)
                            problem = CodebookProblem(PublicInput(text, 'voynich-pilot-v1', 'preserve'), training, capacity=capacity)
                            strategy = CodebookSearch(problem, algorithm=algorithm, seed=seed, width=8, budget=budget)
                            evaluator = CodebookEvaluator(problem)
                            initial = [evaluator(Candidate.create(**s['candidate'])) for s in strategy.pool]
                            refs = []
                            for page, value, role in ((dev, text, 'development'), (frozen, target, 'evaluation')):
                                refs.append(DatasetRef('ZL3b', 'unknown', file_hash(path), digest(value), role,
                                    *page['raw_line_span'], 'certain-words-raw-line-offsets-v1/'+representation,
                                    'Voynich ZL3b '+page['page']))
                            for name, role in (('celsus', 'training'), ('pliny', 'evaluation')):
                                source = corpora[name]; start = int(.3*len(source['text']))
                                refs.append(DatasetRef(name, 'latin', file_hash(source['path']), digest(texts[name]), role,
                                    start, start+len(texts[name]), 'ascii-fold-ae-oe-preserve-ij-uv-v1', source['metadata']['work']))
                            binding = fingerprint({'strategy': strategy.identity(), 'evaluator': evaluator.identity(), 'batch_size': 8})
                            config = dict(representation=representation, capacity=capacity, algorithm=algorithm,
                                          control=control, execution_binding=binding, plan_hash=fingerprint(plan))
                            spec = ExperimentSpec.create(family='voynich-single-symbol', method_version='voynich-pilot-v1',
                                datasets=tuple(refs), configuration=config, environment=env, max_evaluations=budget,
                                seed=seed, retention={'top_k': 3, 'reservoir': 3})
                            print(representation, capacity, seed, algorithm, control, flush=True)
                            result = ExperimentRunner(registry, output/'runs').run(spec, strategy, evaluator, batch_size=8)
                            best = result['top'][0]; candidate = Candidate.create(**best['candidate'])
                            transfer = partial_transfer(replace(problem, public=replace(problem.public, ciphertext=target, role='evaluation')), candidate)
                            row = {**config, 'seed': seed, 'run_id': result['run_id'], 'evaluations': result['evaluations'],
                                'failures': result.get('failures'), 'diagnostics': result['strategy_diagnostics'],
                                'initial_best_loss': min(e.loss for e in initial), 'selected_loss': best['loss'],
                                'key': {labels[c]: u for c, u in candidate.data['key'].items()},
                                'plaintext': best['payload']['plaintext'], 'transfer': transfer,
                                'development_metrics': {n: language_metrics(best['payload']['plaintext'], lm) for n, lm in lms.items()},
                                'transfer_metrics': {n: language_metrics(transfer['plaintext'], lm) for n, lm in lms.items()},
                                'initial_best_metrics': {n: language_metrics(min(initial, key=lambda e:e.loss).payload['plaintext'], lm) for n, lm in lms.items()}}
                            rows.append(row); write_json(output/'rows'/f'{len(rows):03}.json', row)
                            print('RESULT', len(rows), round(best['loss'], 3), flush=True)
        # Independent-author ordinary Latin anchors, never search targets.
        anchors = {}
        for name, source in corpora.items():
            start = int(.85*len(source['text'])); text = source['text'][start:start+600]
            anchors[name] = {'text': text, 'span': [start, start+len(text)],
                             'metrics': {n: language_metrics(text, lm) for n, lm in lms.items()}}
        result = {'plan': plan, 'pages': {'development': dev, 'frozen': frozen}, 'runs': rows,
                  'anchors': anchors, 'total_evaluations': sum(r['evaluations'] for r in rows)}
        write_json(output/'evidence.json', result)
        return result
    finally:
        engine.dispose()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--budget', type=int, default=4096)
    args = parser.parse_args(); run(args.output, args.budget)
