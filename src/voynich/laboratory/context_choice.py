"""Context-conditioned choice between disjoint codeword alternatives (stage 33).

Pages are encoded from last token to first so the successor's codeword is
known; the alternative is chosen by the edge lift between its final glyph and
that codeword's first glyph. The reverse dictionary decodes without the state.
"""
from __future__ import annotations

import math

import numpy as np

from voynich.voynich_core import eva_glyphs

CONTEXT_RULES = ('iid', 'edge', 'edge_max', 'edge_refresh')


def successors(rows):
    """Index of the in-line, no-hard-gap successor of each row, else None."""
    out = []
    for i, row in enumerate(rows):
        nxt = rows[i+1] if i + 1 < len(rows) else None
        out.append(i+1 if nxt is not None and nxt['locus'] == row['locus'] and nxt['start'] == row['end'] + 1 else None)
    return out


def make_encrypt(lift):
    """Return encrypt(book, words, rows, rule, seed) using a {(final, initial): lift} table."""
    def weight(code, following):
        return lift.get((eva_glyphs(code)[-1], eva_glyphs(following)[0]), 1.)

    def encrypt(book, words, rows, rule, seed):
        if rule == 'iid':
            return book.encrypt(words, [r['page'] for r in rows], 'iid', seed)
        if rule not in CONTEXT_RULES or len(words) != len(rows):
            raise ValueError('unknown rule or unaligned rows')
        rng = np.random.default_rng(seed)
        nxt = successors(rows)
        out = [None]*len(words)
        bits = [None]*len(words)
        trajectory = 0.
        informative = context = 0
        state, page = {}, object()
        refresh_events = []

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
            bits[i] = bit
            out[i] = codes[bit]
        audit = dict(choices=bits, refresh_events=refresh_events, trajectory_bits=trajectory,
                     context_choices=context, informative_choices=informative,
                     variant_one_share=sum(bits)/len(bits) if bits else 0)
        return out, audit
    return encrypt
