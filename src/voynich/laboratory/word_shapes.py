"""Dependent word-shape models, scribe-stratified association and edge coupling (stage 31)."""
from __future__ import annotations

from collections import Counter, defaultdict
import heapq
import math
import re

import numpy as np

from voynich.cipher_families import encode
from voynich.experiments.e27_unit_association import strata_indices
from voynich.experiments.e29_frequency_currier_a import BINS
from voynich.laboratory.structured_codes import WordCodebook, glyph_profile
from voynich.voynich_core import TERMINALS, eva_glyphs

START, END, UNK = '^', '$', '?'
MAX_GLYPHS = 15


def page_hands(path):
    """Davis hand ($H) from each IVTFF page header; inline changes are ignored by design."""
    hands = {}
    for raw in path.read_text().splitlines():
        match = re.match(r'^<(f[^.> ]+)>\s*<!([^>]*)>', raw)
        if match:
            hands[match[1]] = dict(re.findall(r'\$(\w)=([^\s>]+)', match[2])).get('H', '?')
    return hands


def stratified_decomposition(tokens, rows, keys, *, seed=2901, permutations=199):
    """Stage-29 additive decomposition with arbitrary strata keys (one per row).

    With keys equal to row sections or (section, roles) this reproduces
    e29.decomposition exactly; tests check that equivalence.
    """
    if not tokens or len(tokens) != len(rows) or len(keys) != len(rows):
        raise ValueError('aligned nonempty tokens, rows and keys required')
    a, b = encode(tokens), encode([r['page'] for r in rows])
    n, nv, npages = len(a), int(a.max()) + 1, int(b.max()) + 1
    counts = np.bincount(a, minlength=nv)
    bins = np.where(counts == 1, 0, np.where(counts <= 4, 1, 2))
    strata = strata_indices(keys)

    def contributions(words):
        result = np.zeros(3)
        for ix in strata:
            joint = np.bincount(words[ix] * npages + b[ix], minlength=nv*npages).reshape(nv, npages)
            w, p = np.nonzero(joint)
            value = joint[w, p]
            pieces = value/n * np.log2(value * len(ix) / (joint.sum(axis=1)[w] * joint.sum(axis=0)[p]))
            result += np.bincount(bins[w], weights=pieces, minlength=3)
        return result

    observed = contributions(a)
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(permutations):
        shuffled = a.copy()
        for ix in strata:
            shuffled[ix] = rng.permutation(a[ix])
        null.append(contributions(shuffled))
    null = np.asarray(null)

    def summary(raw, values):
        mean, sd = float(np.mean(values)), float(np.std(values, ddof=1))
        return dict(raw=float(raw), null_mean=mean, excess=float(raw)-mean, null_sd=sd,
                    null_mean_mcse=sd/np.sqrt(permutations),
                    null_interval=np.quantile(values, [.025, .975]).tolist())

    result = {name: {**summary(observed[i], null[:, i]), 'types': int(np.sum(bins == i)),
                     'token_mass': float(counts[bins == i].sum()/n)} for i, name in enumerate(BINS)}
    return dict(bins=result, total=summary(observed.sum(), null.sum(axis=1)),
                n=n, permutations=permutations, seed=seed)


STRATA = {
    'section': lambda r, h: r['section'],
    'section_hand': lambda r, h: (r['section'], h[r['page']]),
    'roles': lambda r, h: (r['section'], tuple(r['roles'])),
    'roles_hand': lambda r, h: (r['section'], tuple(r['roles']), h[r['page']]),
}


def scribe_measure(tokens, rows, hands):
    out = {name: stratified_decomposition(tokens, rows, [key(r, hands) for r in rows])
           for name, key in STRATA.items()}
    for base in ('section', 'roles'):
        total, within = out[base]['total']['excess'], out[base+'_hand']['total']['excess']
        out[base+'_between_hand'] = total - within
        out[base+'_retained_share'] = within/total if total else None
    out['hands'] = dict(Counter(hands[p] for p in dict.fromkeys(r['page'] for r in rows)))
    return out


def _mi(x, y):
    x, y = encode(x), encode(y)
    nx, ny = int(x.max()) + 1, int(y.max()) + 1
    p = np.bincount(x*ny + y, minlength=nx*ny).reshape(nx, ny)/len(x)
    px, py = p.sum(axis=1, keepdims=True), p.sum(axis=0, keepdims=True)
    m = p > 0
    return float((p[m]*np.log2(p[m]/(px @ py)[m])).sum())


def coupling_records(tokens, rows):
    """(terminal, next initial, page) for in-line adjacent pairs with no hard gap."""
    out = []
    for i in range(len(rows)-1):
        a, b = rows[i], rows[i+1]
        if a['locus'] != b['locus'] or b['start'] != a['end'] + 1:
            continue
        glyphs = eva_glyphs(tokens[i])
        if len(glyphs) < 2 or glyphs[-1] not in TERMINALS:
            continue
        out.append((glyphs[-1], eva_glyphs(tokens[i+1])[0], a['page']))
    return out


def coupling(tokens, rows, *, seed=3101, permutations=199):
    records = coupling_records(tokens, rows)
    if len(records) < 2:
        return dict(n=len(records), raw=0., null_mean=0., excess=0., null_sd=0.)
    terminals = [r[0] for r in records]
    initials = np.array([r[1] for r in records])
    pages = np.array([r[2] for r in records])
    groups = [np.where(pages == p)[0] for p in dict.fromkeys(pages)]
    raw = _mi(terminals, list(initials))
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(permutations):
        shuffled = initials.copy()
        for ix in groups:
            shuffled[ix] = rng.permutation(initials[ix])
        null.append(_mi(terminals, list(shuffled)))
    return dict(n=len(records), raw=raw, null_mean=float(np.mean(null)),
                excess=raw-float(np.mean(null)), null_sd=float(np.std(null, ddof=1)))


def _entropy(counter):
    n = sum(counter.values())
    return -sum(v/n*math.log2(v/n) for v in counter.values()) if n else 0.


def _conditional(pairs):
    joint, left, n = Counter(pairs), Counter(a for a, _ in pairs), len(pairs)
    return -sum(v/n*math.log2(v/left[a]) for (a, _), v in joint.items()) if n else 0.


def shape_diagnostics(words):
    sequences = [eva_glyphs(w) for w in words]
    long = [g for g in sequences if len(g) >= 2]
    glyph = glyph_profile(words)
    return dict(glyph_h=glyph['conditional_entropy'], mean_length=glyph['mean_length'],
                d_last=_entropy(Counter(g[-1] for g in long)) - _conditional([(g[-2], g[-1]) for g in long]),
                d_second=_entropy(Counter(g[1] for g in long)) - _conditional([(g[0], g[1]) for g in long]),
                h_last=_entropy(Counter(g[-1] for g in long)),
                h_last_given_previous=_conditional([(g[-2], g[-1]) for g in long]))


class NGramModel:
    """Glyph n-gram with interpolated Witten-Bell smoothing and start/end symbols."""

    def __init__(self, words, order):
        if order < 1:
            raise ValueError('context length must be positive')
        self.order = order
        self.counts = defaultdict(Counter)
        inventory = set()
        for word in words:
            glyphs = eva_glyphs(word)
            inventory.update(glyphs)
            seq = [START]*order + glyphs + [END]
            for i in range(order, len(seq)):
                for j in range(order+1):
                    self.counts[tuple(seq[i-j:i])][seq[i]] += 1
        self.alphabet = sorted(inventory) + [END, UNK]
        self.index = {g: i for i, g in enumerate(self.alphabet)}
        self._cache = {}

    def distribution(self, context):
        context = tuple(context[-self.order:]) if self.order else ()
        if context in self._cache:
            return self._cache[context]
        if not context:
            lower = np.full(len(self.alphabet), 1/len(self.alphabet))
        else:
            lower = self.distribution(context[1:])
        counts = self.counts.get(context)
        if not counts:
            result = lower
        else:
            total, types = sum(counts.values()), len(counts)
            observed = np.zeros(len(self.alphabet))
            for g, c in counts.items():
                observed[self.index[g]] = c
            result = (observed + types*lower)/(total + types)
        self._cache[context] = result
        return result

    def logprob(self, word):
        glyphs = [g if g in self.index and g not in (END, UNK) else UNK for g in eva_glyphs(word)]
        seq = [START]*self.order + glyphs + [END]
        return sum(math.log2(self.distribution(seq[i-self.order:i])[self.index[seq[i]]])
                   for i in range(self.order, len(seq)))

    def cross_entropy(self, words):
        bits = -sum(self.logprob(w) for w in words)
        return bits / sum(len(eva_glyphs(w)) + 1 for w in words)

    def _sampling(self, context):
        p = self.distribution(context).copy()
        p[self.index[UNK]] = 0
        return p/p.sum()

    def sample(self, rng):
        while True:
            seq = [START]*self.order
            while True:
                g = self.alphabet[int(rng.choice(len(self.alphabet), p=self._sampling(seq)))]
                if g == END or len(seq) - self.order > MAX_GLYPHS:
                    break
                seq.append(g)
            glyphs = seq[self.order:]
            if g == END and 1 <= len(glyphs) <= MAX_GLYPHS:
                return ''.join(glyphs)

    def top(self, k):
        """Exact k most probable strings (1..MAX_GLYPHS glyphs, no UNK) by best-first search."""
        heap, out = [(0., (), False)], []
        while heap and len(out) < k:
            cost, glyphs, complete = heapq.heappop(heap)
            if complete:
                out.append((''.join(glyphs), -cost))
                continue
            p = self.distribution([START]*self.order + list(glyphs))
            for i, g in enumerate(self.alphabet):
                if g == UNK or p[i] <= 0:
                    continue
                step = cost - math.log2(p[i])
                if g == END:
                    if glyphs:
                        heapq.heappush(heap, (step, glyphs, True))
                elif len(glyphs) < MAX_GLYPHS:
                    heapq.heappush(heap, (step, glyphs + (g,), False))
        return out

    def description(self):
        return dict(order=self.order, alphabet=self.alphabet,
                    counts={' '.join(k) if k else '': dict(sorted(v.items())) for k, v in sorted(self.counts.items())})


def folio_cv(words_by_folio, order):
    """Leave-one-folio-out cross-entropy, pooled bits per glyph including end."""
    bits = glyphs = 0
    for held in words_by_folio:
        train = [w for folio, ws in words_by_folio.items() if folio != held for w in ws]
        model = NGramModel(train, order)
        bits -= sum(model.logprob(w) for w in words_by_folio[held])
        glyphs += sum(len(eva_glyphs(w)) + 1 for w in words_by_folio[held])
    return bits/glyphs


def model_codebook(vocabulary, model, seed):
    """Successive sampling without replacement proportional to model probability."""
    vocabulary = sorted(set(vocabulary))
    rng = np.random.default_rng(seed)
    seen, draws = {}, 0
    while len(seen) < 2*len(vocabulary):
        word = model.sample(rng)
        draws += 1
        seen.setdefault(word, None)
    codes = list(seen)
    order = rng.permutation(len(codes))
    codes = [codes[int(i)] for i in order]
    return WordCodebook({w: [codes[2*i], codes[2*i+1]] for i, w in enumerate(vocabulary)}), draws
