"""Bounded edge/interior word codebooks and auditable binary choice policies."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import itertools
import json
import math

import numpy as np

from voynich.voynich_core import eva_glyphs

RULES = ('iid', 'page', 'word_page', 'refresh')


def serialized_bits(value):
    return 8*len(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


@dataclass
class SlotGrammar:
    slots: list[list[tuple[tuple[str, ...], int]]]
    weights: dict[str, float]
    combinations: int

    @classmethod
    def from_slots(cls, slots):
        weights = defaultdict(float)
        combinations = 0
        for entries in itertools.product(*slots):
            word = ''.join(g for part, _ in entries for g in part)
            weights[word] += math.prod(count for _, count in entries)
            combinations += 1
        return cls(slots, dict(sorted(weights.items())), combinations)

    @classmethod
    def fit(cls, words):
        counters = [Counter(), Counter(), Counter()]
        for word in words:
            glyphs = tuple(eva_glyphs(word))
            if not 2 <= len(glyphs) <= 10:
                continue
            for c, part in zip(counters, (glyphs[:1], glyphs[1:-1], glyphs[-1:])):
                c[part] += 1
        slots = [sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
                 for c, limit in zip(counters, (16, 64, 16))]
        return cls.from_slots(slots)

    def description(self):
        return dict(slots=self.slots, combinations=self.combinations,
                    unique_support=len(self.weights), collisions=self.combinations-len(self.weights),
                    maximum_support_bits=math.log2(len(self.weights)) if self.weights else 0,
                    serialization_bits=serialized_bits(self.slots))

    def coverage(self, tokens, seen=()):
        types = set(tokens)
        unseen = types-set(seen)
        return dict(token=sum(w in self.weights for w in tokens)/len(tokens),
                    type=sum(w in self.weights for w in types)/len(types),
                    unseen_types=len(unseen),
                    unseen_type=sum(w in self.weights for w in unseen)/len(unseen) if unseen else None)


@dataclass
class WordCodebook:
    encode: dict[str, list[str]]

    def __post_init__(self):
        all_codes = [c for codes in self.encode.values() for c in codes]
        if any(len(codes) != 2 for codes in self.encode.values()) or len(set(all_codes)) != len(all_codes):
            raise ValueError('exactly two globally distinct alternatives per word required')

    @classmethod
    def make(cls, vocabulary, grammar, seed):
        vocabulary = sorted(set(vocabulary))
        n = 2*len(vocabulary)
        if len(grammar.weights) < n:
            raise ValueError(f'insufficient grammar support: {len(grammar.weights)} < {n}')
        rng = np.random.default_rng(seed)
        codes = list(grammar.weights)
        weights = np.array(list(grammar.weights.values()), dtype=float)
        sample = rng.choice(len(codes), size=n, replace=False, p=weights/weights.sum())
        rng.shuffle(sample)
        return cls({w: [codes[int(sample[2*i])], codes[int(sample[2*i+1])]]
                    for i, w in enumerate(vocabulary)})

    def decrypt(self, ciphertext):
        reverse = {code: word for word, codes in self.encode.items() for code in codes}
        return [reverse[c] for c in ciphertext]

    def costs(self):
        m = 2*len(self.encode)
        return dict(entries=len(self.encode), codewords=m,
                    dictionary_serialization_bits=serialized_bits(self.encode),
                    uniform_ordered_assignment_reference_bits=math.lgamma(m+1)/math.log(2))

    def encrypt(self, words, pages, rule, seed):
        if rule not in RULES or len(words) != len(pages):
            raise ValueError('unknown policy or unaligned pages')
        rng = np.random.default_rng(seed)
        current_page = object()
        state = {}
        bits = []
        refresh_events = []
        choice_count = 0
        trajectory_bits = 0.
        peak = 0
        page_bit = 0
        for i, (word, page) in enumerate(zip(words, pages)):
            if page != current_page:
                current_page = page
                state = {}
                if rule == 'page':
                    page_bit = int(rng.integers(2))
                    choice_count += 1
                    trajectory_bits += 1
            if rule == 'page':
                bit = page_bit
                peak = 1
            elif rule == 'iid':
                bit = int(rng.integers(2))
                choice_count += 1
                trajectory_bits += 1
            else:
                refresh = word not in state
                if rule == 'refresh' and not refresh:
                    refresh = bool(rng.random() < .25)
                    refresh_events.append([i, refresh])
                    trajectory_bits -= math.log2(.25 if refresh else .75)
                if refresh:
                    state[word] = int(rng.integers(2))
                    choice_count += 1
                    trajectory_bits += 1
                bit = state[word]
                peak = max(peak, len(state))
            bits.append(bit)
        output = [self.encode[word][bit] for word, bit in zip(words, bits)]
        audit = dict(choices=bits, refresh_events=refresh_events, fair_bit_draws=choice_count,
                     trajectory_bits=trajectory_bits, peak_variant_state_bits=peak,
                     variant_one_share=sum(bits)/len(bits) if bits else 0)
        return output, audit


def glyph_profile(tokens):
    sequences = [eva_glyphs(w) for w in tokens]
    joint = Counter((a, b) for gs in sequences for a, b in zip(gs, gs[1:]))
    left = Counter()
    for (a, b), n in joint.items():
        left[a] += n
    total = sum(joint.values())
    entropy = -sum(n/total*math.log2(n/left[a]) for (a, _), n in joint.items()) if total else 0.
    return dict(mean_length=sum(map(len, sequences))/len(tokens), conditional_entropy=entropy)


def control_indices(rows, kind, seed):
    """Reorder rows and their tokens together; preserve page/role membership."""
    rng = np.random.default_rng(seed)
    order = np.arange(len(rows))
    if kind == 'word':
        groups = defaultdict(list)
        for i, row in enumerate(rows):
            groups[(row['page'], tuple(row['roles']))].append(i)
        for ix in groups.values():
            order[ix] = rng.permutation(ix)
    elif kind == 'line':
        pages = defaultdict(list)
        for i, row in enumerate(rows):
            pages[row['page']].append(i)
        for indices in pages.values():
            chunks = []
            for i in indices:
                if not chunks or rows[chunks[-1][-1]]['locus'] != rows[i]['locus']:
                    chunks.append([])
                chunks[-1].append(i)
            classes = defaultdict(list)
            for i, chunk in enumerate(chunks):
                classes[bool(rows[chunk[0]]['roles'][2])].append(i)
            replaced = list(chunks)
            for positions in classes.values():
                for dest, src in zip(positions, rng.permutation(positions)):
                    replaced[dest] = chunks[int(src)]
            order[indices] = [i for chunk in replaced for i in chunk]
    else:
        raise ValueError('unknown control')
    return order


def lag_rates(tokens, rows):
    groups = defaultdict(list)
    for word, row in zip(tokens, rows):
        groups[row['page']].append(word)
    values = []
    for lag in (1, 4, 16):
        pairs = [(ws[i-lag], ws[i]) for ws in groups.values() for i in range(lag, len(ws))]
        values.append(sum(a == b for a, b in pairs)/len(pairs) if pairs else 0.)
    return np.array(values)


def order_diagnostic(tokens, rows):
    observed = lag_rates(tokens, rows)
    result = dict(observed=observed.tolist(), lags=[1, 4, 16])
    for kind in ('word', 'line'):
        nulls = []
        moved = []
        for seed in range(3001, 3020):
            indices = control_indices(rows, kind, seed)
            shuffled = [tokens[int(i)] for i in indices]
            new_rows = [rows[int(i)] for i in indices]
            nulls.append(lag_rates(shuffled, new_rows))
            moved.append(len({rows[i]['locus'] for i, j in enumerate(indices) if i != j}))
        nulls = np.array(nulls)
        result[kind] = dict(null_mean=nulls.mean(axis=0).tolist(), null_sd=nulls.std(axis=0, ddof=1).tolist(),
                            excess=(observed-nulls.mean(axis=0)).tolist(), moved_line_counts=moved)
    return result
