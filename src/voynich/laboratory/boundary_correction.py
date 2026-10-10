"""Corrected neighbour rule, coupling, context choice and enumeration (post hoc correction of stages 31-34).

Stages 31-34 treated consecutive word indices on a line as neighbours, which
wrongly includes words separated by a drawing. Here neighbours additionally
require the transcribed gap after the left word to be ordinary or uncertain.
The original modules are left unchanged so their committed results replay.
"""
from __future__ import annotations

import heapq
import math

import numpy as np

from voynich.experiments.e30_structured_word_codes import profile as stage30_profile
from voynich.laboratory.word_shapes import END, MAX_GLYPHS, START, UNK, _mi
from voynich.voynich_core import TERMINALS, eva_glyphs

NEIGHBOUR_GAPS = ('ordinary', 'uncertain')
CONTEXT_RULES = ('iid', 'edge', 'edge_max', 'edge_refresh')


def annotate(rows, lines_by_locus):
    """Copy rows adding gap_after: the transcribed gap after each token's last word (None at line end)."""
    out = []
    for row in rows:
        gaps = lines_by_locus[row['locus']]['gaps']
        out.append(dict(row, gap_after=gaps[row['end']] if row['end'] < len(gaps) else None))
    return out


def neighbours(rows):
    out = []
    for i, row in enumerate(rows):
        nxt = rows[i+1] if i + 1 < len(rows) else None
        ok = (nxt is not None and nxt['locus'] == row['locus'] and nxt['start'] == row['end'] + 1
              and row['gap_after'] in NEIGHBOUR_GAPS)
        out.append(i+1 if ok else None)
    return out


def coupling_records(tokens, rows):
    out = []
    for i, j in enumerate(neighbours(rows)):
        if j is None:
            continue
        glyphs = eva_glyphs(tokens[i])
        if len(glyphs) >= 2 and glyphs[-1] in TERMINALS:
            out.append((glyphs[-1], eva_glyphs(tokens[j])[0], rows[i]['page']))
    return out


def coupling(tokens, rows, *, seed=3101, permutations=199):
    """Stage-31 coupling statistic with the corrected neighbour rule."""
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


def profile(tokens, rows):
    out = stage30_profile(tokens, rows)
    out['coupling'] = coupling(tokens, rows)
    out['vector'] = out['vector'] + [out['coupling']['excess']]
    return out


def canonical_top(model, k):
    """Exact k most probable distinct strings, counting only canonical glyph paths."""
    heap, out, seen = [(0., (), False)], [], set()
    while heap and len(out) < k:
        cost, glyphs, complete = heapq.heappop(heap)
        if complete:
            word = ''.join(glyphs)
            if word not in seen:
                seen.add(word)
                out.append((word, -cost))
            continue
        p = model.distribution([START]*model.order + list(glyphs))
        for i, g in enumerate(model.alphabet):
            if g == UNK or p[i] <= 0:
                continue
            step = cost - math.log2(p[i])
            if g == END:
                if glyphs and tuple(eva_glyphs(''.join(glyphs))) == glyphs:
                    heapq.heappush(heap, (step, glyphs, True))
            elif len(glyphs) < MAX_GLYPHS:
                heapq.heappush(heap, (step, glyphs + (g,), False))
    return out


def page_encrypt(book, words, rows, rule, seed):
    return book.encrypt(words, [r['page'] for r in rows], rule, seed)


def make_context_encrypt(lift):
    """Stage-33 choice rules with the corrected neighbour rule (logic otherwise identical)."""
    def weight(code, following):
        return lift.get((eva_glyphs(code)[-1], eva_glyphs(following)[0]), 1.)

    def encrypt(book, words, rows, rule, seed):
        if rule == 'iid':
            return book.encrypt(words, [r['page'] for r in rows], 'iid', seed)
        if rule not in CONTEXT_RULES or len(words) != len(rows):
            raise ValueError('unknown rule or unaligned rows')
        rng = np.random.default_rng(seed)
        nxt = neighbours(rows)
        out, bits = [None]*len(words), [None]*len(words)
        trajectory, informative, context = 0., 0, 0
        state, page, refresh_events = {}, object(), []

        def choose(i, codes):
            nonlocal trajectory, informative, context
            if nxt[i] is None:
                trajectory += 1
                return int(rng.integers(2))
            context += 1
            w = [weight(c, out[nxt[i]]) for c in codes]
            if w[0] != w[1]:
                informative += 1
            if rule == 'edge_max':
                if w[0] == w[1]:
                    trajectory += 1
                    return int(rng.integers(2))
                return int(w[1] > w[0])
            p1 = w[1]/(w[0]+w[1])
            bit = int(rng.random() < p1)
            trajectory -= math.log2(p1 if bit else 1-p1)
            return bit

        for i in range(len(words)-1, -1, -1):
            if rows[i]['page'] != page:
                page, state = rows[i]['page'], {}
            word, codes = words[i], book.encode[words[i]]
            if rule == 'edge_refresh':
                fresh = word not in state
                if not fresh:
                    fresh = bool(rng.random() < .25)
                    refresh_events.append([i, fresh])
                    trajectory -= math.log2(.25 if fresh else .75)
                if fresh:
                    state[word] = choose(i, codes)
                bit = state[word]
            else:
                bit = choose(i, codes)
            bits[i], out[i] = bit, codes[bit]
        return out, dict(choices=bits, refresh_events=refresh_events, trajectory_bits=trajectory,
                         context_choices=context, informative_choices=informative,
                         variant_one_share=sum(bits)/len(bits) if bits else 0)
    return encrypt
