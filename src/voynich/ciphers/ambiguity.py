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
