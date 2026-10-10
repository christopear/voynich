"""Truth-free, exhaustive elementary moves for capacity-constrained codebooks."""
from collections import Counter
from itertools import combinations
import random

from voynich.search.strategies import Candidate


def neighbors(candidate, units, capacity):
    data = candidate.data
    key = data['key']
    counts = Counter(key.values())
    if not key or any(v not in units for v in key.values()) or max(counts.values()) > capacity:
        raise ValueError('invalid starting key')
    for symbol in sorted(key):
        for unit in sorted(set(units)):
            if unit != key[symbol] and counts[unit] < capacity:
                yield Candidate.create(**{**data, 'key': {**key, symbol: unit}})
    for a, b in combinations(sorted(key), 2):
        if key[a] != key[b]:
            yield Candidate.create(**{**data, 'key': {**key, a: key[b], b: key[a]}})


def total(evaluation):
    if not evaluation.score.valid:
        raise ValueError('invalid candidate evaluation')
    return sum(value for _, value in evaluation.score.components)


def record(candidate, evaluation):
    return dict(candidate=candidate.data, total_bits=total(evaluation),
                components=dict(evaluation.score.components), payload=evaluation.payload)


def audit(evaluator, candidate, units, capacity=2, cap=3000):
    moves = list(neighbors(candidate, units, capacity))
    if len(moves) + 1 > cap:
        raise ValueError('complete neighborhood exceeds preregistered cap')
    center = evaluator(candidate)
    best_candidate, best = candidate, center
    improving = 0
    for move in moves:
        result = evaluator(move)
        improving += total(result) < total(center) - 1e-9
        if total(result) < total(best) - 1e-9:
            best_candidate, best = move, result
    return dict(center=record(candidate, center), best=record(best_candidate, best),
                evaluations=1+len(moves), improving_neighbors=improving, complete=True)


def descend(evaluator, candidate, units, *, algorithm, budget, seed=39001, capacity=2):
    """Bounded greedy continuation. No known key or plaintext enters selection."""
    if algorithm not in ('systematic', 'random') or budget < 1:
        raise ValueError('invalid continuation configuration')
    rng = random.Random(seed)
    incumbent = candidate
    value = evaluator(incumbent)
    calls, steps = 1, 0
    history = [total(value)]
    stopped = 'budget'
    incomplete = False
    moves = list(neighbors(incumbent, units, capacity))
    while calls < budget and moves:
        if algorithm == 'random':
            proposal = rng.choice(moves)
            result = evaluator(proposal)
            calls += 1
            if total(result) < total(value) - 1e-9:
                incumbent, value = proposal, result
                steps += 1
                history.append(total(value))
                moves = list(neighbors(incumbent, units, capacity))
            continue
        best, best_value = incumbent, value
        evaluated = 0
        for proposal in moves:
            if calls == budget:
                break
            result = evaluator(proposal)
            calls += 1
            evaluated += 1
            if total(result) < total(best_value) - 1e-9:
                best, best_value = proposal, result
        incomplete = evaluated != len(moves)
        if total(best_value) < total(value) - 1e-9:
            incumbent, value = best, best_value
            steps += 1
            history.append(total(value))
        elif not incomplete:
            stopped = 'local_optimum'
            break
        if incomplete:
            break
        moves = list(neighbors(incumbent, units, capacity))
    if not moves:
        stopped = 'no_moves'
    return dict(best=record(incumbent, value), evaluations=calls, accepted_steps=steps,
                total_bits_history=history, stopped=stopped, incomplete_sweep=incomplete,
                algorithm=algorithm, budget=budget, seed=seed)
