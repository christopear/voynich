"""Small exhaustive oracle for testing ambiguity claims, never a production solver."""
from dataclasses import dataclass
import math
from .contracts import DecodingOutcome


@dataclass(frozen=True)
class AmbiguousResult:
    outcome: DecodingOutcome
    masses: tuple[tuple[str, float], ...]
    mass_interpretation: str


def enumerate_paths(ciphertext: str, entries: tuple[tuple[str, str, float], ...], *,
                    max_paths: int = 10000) -> AmbiguousResult:
    """Weights multiply along paths and sum per plaintext; no normalization.

    These are path-model weights, not calibrated plaintext probabilities.
    A work bound limits both visited partial paths and completed paths.
    """
    if not ciphertext or max_paths < 1 or not entries:
        raise ValueError("nonempty input/entries and positive work bound required")
    if any(not code or not unit or not math.isfinite(weight) or not 0 <= weight <= 1
           for code, unit, weight in entries):
        raise ValueError("invalid transition")
    stack = [(0, "", 1.0)]
    masses, path_count, visited = {}, 0, 0
    furthest = 0
    while stack and visited < max_paths:
        position, plain, mass = stack.pop()
        visited += 1
        furthest = max(furthest, position)
        if position == len(ciphertext):
            masses[plain] = masses.get(plain, 0) + mass
            path_count += 1
        else:
            for code, unit, weight in reversed(entries):
                if ciphertext.startswith(code, position):
                    stack.append((position + len(code), plain + unit, mass * weight))
    pruned = bool(stack)
    status = "unresolved" if pruned else (
        "no-valid-path" if not masses else "unique-plaintext" if len(masses) == 1 else "multiple-plaintexts")
    return AmbiguousResult(DecodingOutcome(tuple(sorted(masses)), status,
        furthest / len(ciphertext), path_count, not pruned, pruned,
        "lower-bound" if pruned else "exact"), tuple(sorted(masses.items())),
        "retained path weight; not calibrated probability" if pruned else "exact sum under declared path weights")


def count_mapping_completions(known_mapping: dict[str,str], units: tuple[str,...],
                              capacity: int, unknown_codes: int) -> int:
    """Exact count of assignments to distinct unseen codes under capacity bounds.

    Conditions on the supplied key and a fixed segmentation policy. It does not
    choose a completion, use reserved language evidence, or assign probabilities.
    Only letters/pairs are supported: word-position constraints need extra state.
    Other encoder rules, including greedy unitization, are not applied: this
    count is an upper bound when those additional constraints are required.
    """
    from collections import Counter
    if capacity<1 or unknown_codes<0 or len(set(units))!=len(units) or not units:
        raise ValueError('invalid completion problem')
    if any(not u or len(u)>2 or ' ' in u for u in units):
        raise NotImplementedError('completion counting supports letters/pairs only')
    counts=Counter(known_mapping.values())
    if set(counts)-set(units) or any(n>capacity for n in counts.values()):
        raise ValueError('known key violates declared inventory/capacity')
    if unknown_codes>sum(capacity-counts[u] for u in units):return 0
    ways=[1]+[0]*unknown_codes
    for unit in units:
        remaining=capacity-counts[unit]
        updated=[0]*(unknown_codes+1)
        for assigned,number in enumerate(ways):
            for new in range(min(remaining,unknown_codes-assigned)+1):
                updated[assigned+new]+=number*math.comb(assigned+new,new)
        ways=updated
    return ways[unknown_codes]
