"""Public-input-only, all-survivor beam search followed by frozen continuation."""
from voynich.search.codebooks import CodebookSearch
from voynich.search.grouped import GroupedProblem, GroupedEvaluator, screen_policies
from voynich.search.neighborhood import descend, record
from voynich.search.strategies import Candidate


def beam(problem, seed, budget=4096, width=8):
    strategy = CodebookSearch(problem, algorithm='beam', seed=seed, width=width, budget=budget)
    evaluator = GroupedEvaluator(problem)
    best = None
    invalid = 0
    while proposals := strategy.propose(width):
        scores = [evaluator(c) for c in proposals]
        strategy.observe(scores)
        for candidate, score in zip(proposals, scores):
            if score.loss is None:
                invalid += 1
                continue
            rank = (score.loss, candidate.id)
            if best is None or rank < best[0]:
                best = (rank, candidate, score)
    if best is None:
        raise ValueError('no valid beam candidate')
    return dict(best=record(best[1], best[2]), loss=best[2].loss,
                candidate_id=best[1].id, evaluations=strategy.evaluated, invalid=invalid)


def recover(spans, training, spacing, seed, *, policy_cap=64, beam_budget=4096,
            continuation_budget=8192, progress=None):
    screen = screen_policies(spans, training, spacing)
    policies = sorted(screen['survivors'], key=lambda p: p['prefixes'])
    if not policies or len(policies) > policy_cap:
        return dict(status='no_parsers' if not policies else 'parser_budget_cap',
                    screen=screen, evaluations=0, policies=[])
    winners = []
    for index, policy in enumerate(policies):
        problem = GroupedProblem(tuple(spans), training, tuple(policy['prefixes']), spacing)
        winner = dict(policy=policy, **beam(problem, seed, budget=beam_budget))
        winners.append(winner)
        if progress:
            progress(index, len(policies), winner)
    selected = min(winners, key=lambda w: (w['loss'], w['policy']['prefixes'], w['candidate_id']))
    problem = GroupedProblem(tuple(spans), training, tuple(selected['policy']['prefixes']), spacing)
    refined = descend(GroupedEvaluator(problem), Candidate.create(**selected['best']['candidate']),
                      problem.units, algorithm='random', budget=continuation_budget, seed=39001+seed)
    return dict(status='completed', screen=screen, policies=winners, selected=selected,
                refined=refined, evaluations=sum(w['evaluations'] for w in winners)+refined['evaluations'])
