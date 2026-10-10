"""Annealing over the same elementary moves as greedy neighborhood descent."""
from collections import Counter
from itertools import combinations
import random

from voynich.search.neighborhood import record, total
from voynich.search.strategies import Candidate


def move_descriptors(candidate, units, capacity=2):
    key = candidate.data['key']
    counts = Counter(key.values())
    if not key or any(v not in units for v in key.values()) or max(counts.values()) > capacity:
        raise ValueError('invalid starting key')
    return ([('assign', symbol, unit) for symbol in sorted(key) for unit in sorted(set(units))
             if unit != key[symbol] and counts[unit] < capacity] +
            [('swap', a, b) for a, b in combinations(sorted(key), 2) if key[a] != key[b]])


def apply_move(candidate, move):
    data = candidate.data
    key = dict(data['key'])
    kind, a, b = move
    if kind == 'assign':
        key[a] = b
    elif kind == 'swap':
        key[a], key[b] = key[b], key[a]
    else:
        raise ValueError('unknown move')
    return Candidate.create(**{**data, 'key': key})


def anneal(evaluator, candidate, units, *, budget=8192, seed=39001, acceptance_seed=49001):
    if budget < 2:
        raise ValueError('annealing needs at least two evaluations')
    proposals, acceptance = random.Random(seed), random.Random(acceptance_seed)
    current = best = candidate
    current_value = best_value = evaluator(candidate)
    moves = move_descriptors(current, units)
    calls, uphill, accepted = 1, 0, 0
    history = [dict(evaluations=1, total_bits=total(best_value))]
    while calls < budget and moves:
        temperature = 12*(.2/12)**((calls-1)/max(1, budget-2))
        proposal = apply_move(current, proposals.choice(moves))
        value = evaluator(proposal)
        calls += 1
        delta = total(value)-total(current_value)
        if delta <= 0 or acceptance.random() < 2**(-delta/temperature):
            uphill += delta > 0
            accepted += 1
            current, current_value = proposal, value
            moves = move_descriptors(current, units)
        if total(value) < total(best_value)-1e-9:
            best, best_value = proposal, value
            history.append(dict(evaluations=calls, total_bits=total(value)))
    return dict(best=record(best, best_value), evaluations=calls, accepted_moves=accepted,
                uphill_moves=uphill, best_history=history, proposal_seed=seed,
                acceptance_seed=acceptance_seed, temperature=[12, .2])
