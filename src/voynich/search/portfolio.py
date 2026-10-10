"""Equal-total-budget independent greedy and annealing trajectories."""
from voynich.search.key_escape import anneal
from voynich.search.neighborhood import descend
from voynich.search.strategies import Candidate


def portfolio(evaluator, start, units, *, budget=8192, seed=39001, acceptance_seed=49001):
    if budget < 4 or budget % 2:
        raise ValueError('portfolio requires an even budget of at least four')
    greedy = descend(evaluator, start, units, algorithm='random', budget=budget//2, seed=seed)
    thermal = anneal(evaluator, start, units, budget=budget//2, seed=seed, acceptance_seed=acceptance_seed)
    arms = {'greedy': greedy, 'annealing': thermal}
    selected = min(arms, key=lambda name: (arms[name]['best']['total_bits'],
                   Candidate.create(**arms[name]['best']['candidate']).id))
    return dict(best=arms[selected]['best'], selected_arm=selected, arms=arms,
                evaluations=sum(a['evaluations'] for a in arms.values()))


def stability(records):
    """Public-output agreement; never a correctness claim on its own."""
    if len(records) != 3 or any(r is None for r in records):
        return dict(flag=False, minimum_agreement=None, reason='incomplete')
    if len({tuple(r['prefixes']) for r in records}) != 1:
        return dict(flag=False, minimum_agreement=None, reason='parser_disagreement')
    texts = [r['plaintext'].replace('\n', '') for r in records]
    if len({len(t) for t in texts}) != 1:
        return dict(flag=False, minimum_agreement=None, reason='length_disagreement')
    values = []
    for i, a in enumerate(texts):
        for b in texts[i+1:]:
            pairs = [(x, y) for x, y in zip(a, b) if x != ' ' or y != ' ']
            values.append(sum(x == y for x, y in pairs)/max(1, len(pairs)))
    minimum = min(values)
    return dict(flag=minimum >= .95, minimum_agreement=minimum, reason='measured')
