#!/usr/bin/env python3
"""
Voynich visible-to-hidden boundary test
=======================================

Question
--------
Does a terminal-selection rule learned ONLY from visible spaces also predict
the terminal at candidate boundaries INSIDE written Voynich tokens?

Training data
-------------
For every visibly spaced pair:

    LEFT RIGHT

where LEFT ends in EVA n/l/r, learn:

    P(terminal | stem)
    P(terminal | stem, initial(RIGHT))

Example:

    chol oly
     ^

LEFT = chol
stem = cho
terminal = l
initial(RIGHT) = o

Hidden-boundary candidates
--------------------------
For rare long written tokens AB, propose an internal boundary A|B only when:

  * the token occurs <= 2 times
  * it is >= 6 EVA glyph-units long
  * A and B are independently attested >= 5 times
  * A ends in n/l/r
  * both sides contain at least two EVA glyph-units

If several splits are possible, choose the one maximizing:

    freq(A) * freq(B)

Evaluation
----------
Predict the observed terminal at A|B using:

  1. stem only
  2. stem + initial(B)

The second model is trained ONLY from visible boundaries.

Expected result on the ZL3b transcription used in our analysis:
approximately

    candidate internal boundaries: 769

    stem + next initial:
        evaluable = 624
        accuracy  = 0.708

    stem only:
        evaluable = 769
        accuracy  = 0.645

    on the SAME 624 examples:
        stem + next initial = 0.708
        stem only           = 0.639

Minor differences can occur if the transcription/version or token-cleaning
rules differ.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TERMINALS = ("n", "l", "r")

# EVA compounds treated as single glyph-units in this experiment.
# Order longest-first is intentional.
COMPOUND_GLYPHS = (
    "cth",
    "ckh",
    "cph",
    "cfh",
    "ch",
    "sh",
)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

@dataclass
class Line:
    locus: str
    page: str
    tokens: list[str]


def parse_tokens(text: str) -> list[str]:
    """
    Reproduce the fairly conservative token cleaning used in the exploration.

    Important:
    - <-> is treated as a token boundary.
    - IVTFF markup is removed.
    - uncertain alternatives like [foo:bar] retain the first reading.
    - punctuation separates tokens.
    """
    text = text.replace("<->", " ")

    # Remove inline comments / IVTFF markup.
    text = re.sub(r"<!.*?>", " ", text)
    text = re.sub(r"<%>|<\$>|<~>", " ", text)

    # Keep first branch of alternative readings.
    text = re.sub(
        r"\[([a-z']+):[^\]]+\]",
        r"\1",
        text,
        flags=re.IGNORECASE,
    )

    # Remove braces but preserve their contents.
    text = re.sub(r"\{([^}]*)\}", r"\1", text)

    # Remove IVTFF @-references.
    text = re.sub(r"@\d+;", " ", text)

    text = text.replace("?", "")
    text = text.replace("'", "").replace("’", "")
    text = text.lower()

    raw = re.split(r"[.,\s=<>-]+", text)

    out = []
    for x in raw:
        x = re.sub(r"[^a-z]", "", x)
        if x:
            out.append(x)
    return out


def load_zl3b(path: Path) -> list[Line]:
    """
    Read paragraph/body text lines from a ZL3b IVTFF transcription.
    """
    lines: list[Line] = []

    locus_re = re.compile(
        r"^<(f[^.>]+\.\d+),([^>]*)>\s*(.*)$"
    )

    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            m = locus_re.match(raw.rstrip("\n"))
            if not m:
                continue

            locus, descriptor, body = m.groups()

            # We used normal paragraph/body text only.
            if "P" not in descriptor:
                continue

            tokens = parse_tokens(body)
            if not tokens:
                continue

            page = locus.split(".")[0]

            lines.append(
                Line(
                    locus=locus,
                    page=page,
                    tokens=tokens,
                )
            )

    return lines


# ---------------------------------------------------------------------------
# EVA glyph handling
# ---------------------------------------------------------------------------

def glyphs(word: str) -> list[str]:
    """
    Convert EVA transcription string into the glyph-units used in the test.

    This is deliberately NOT claiming these units are plaintext characters.
    It merely avoids splitting common EVA compound glyphs such as 'ch'/'cth'.
    """
    out: list[str] = []
    i = 0

    while i < len(word):
        hit = None

        for compound in COMPOUND_GLYPHS:
            if word.startswith(compound, i):
                hit = compound
                break

        if hit is not None:
            out.append(hit)
            i += len(hit)
        else:
            out.append(word[i])
            i += 1

    return out


def first_glyph(word: str) -> str:
    g = glyphs(word)
    return g[0] if g else ""


# ---------------------------------------------------------------------------
# Learn visible-space terminal rule
# ---------------------------------------------------------------------------

TerminalCounts = dict[str, int]


def empty_terminal_counts() -> dict[str, int]:
    return {x: 0 for x in TERMINALS}


@dataclass
class VisibleBoundaryModel:
    # stem -> terminal counts
    stem_counts: dict[str, dict[str, int]]

    # stem -> next-initial -> terminal counts
    stem_next_counts: dict[str, dict[str, dict[str, int]]]


def learn_from_visible_spaces(lines: Iterable[Line]) -> VisibleBoundaryModel:
    """
    Train exclusively on ordinary visible within-line token boundaries.

    For:

        token_i token_{i+1}

    if token_i ends n/l/r:

        stem = token_i[:-1]
        terminal = token_i[-1]
        next_initial = first EVA glyph of token_{i+1}
    """
    stem_counts = defaultdict(empty_terminal_counts)

    stem_next_counts = defaultdict(
        lambda: defaultdict(empty_terminal_counts)
    )

    for line in lines:
        ts = line.tokens

        for i in range(len(ts) - 1):
            left = ts[i]
            right = ts[i + 1]

            if len(left) < 2:
                continue

            terminal = left[-1]

            if terminal not in TERMINALS:
                continue

            stem = left[:-1]
            next_initial = first_glyph(right)

            stem_counts[stem][terminal] += 1
            stem_next_counts[stem][next_initial][terminal] += 1

    return VisibleBoundaryModel(
        stem_counts=dict(stem_counts),
        stem_next_counts={
            stem: dict(v)
            for stem, v in stem_next_counts.items()
        },
    )


# ---------------------------------------------------------------------------
# Infer candidate hidden boundaries
# ---------------------------------------------------------------------------

@dataclass
class HiddenBoundary:
    joined: str

    left: str
    right: str

    stem: str
    terminal: str
    next_initial: str

    left_freq: int
    right_freq: int

    split_glyph_index: int


def corpus_frequencies(lines: Iterable[Line]) -> Counter:
    c = Counter()

    for line in lines:
        c.update(line.tokens)

    return c


def infer_hidden_boundaries(
    freq: Counter,
    *,
    max_joined_frequency: int = 2,
    min_joined_glyphs: int = 6,
    min_component_frequency: int = 5,
    min_component_glyphs: int = 2,
) -> list[HiddenBoundary]:
    """
    Find rare long written tokens that plausibly consist of A|B.

    Crucially, this segmentation procedure does NOT use the
    visible-boundary terminal prediction tables.

    That keeps the test meaningful:
        boundary discovery and terminal prediction are separate.
    """
    out: list[HiddenBoundary] = []

    for joined, joined_freq in freq.items():

        if joined_freq > max_joined_frequency:
            continue

        gs = glyphs(joined)

        if len(gs) < min_joined_glyphs:
            continue

        candidates = []

        # Require >=2 glyph-units on both sides.
        for i in range(
            min_component_glyphs,
            len(gs) - min_component_glyphs + 1,
        ):
            left = "".join(gs[:i])
            right = "".join(gs[i:])

            if freq[left] < min_component_frequency:
                continue

            if freq[right] < min_component_frequency:
                continue

            if len(left) < 2:
                continue

            terminal = left[-1]

            if terminal not in TERMINALS:
                continue

            # Original heuristic:
            # prefer splits whose two components are independently common.
            score = freq[left] * freq[right]

            candidates.append(
                (
                    score,
                    HiddenBoundary(
                        joined=joined,
                        left=left,
                        right=right,
                        stem=left[:-1],
                        terminal=terminal,
                        next_initial=first_glyph(right),
                        left_freq=freq[left],
                        right_freq=freq[right],
                        split_glyph_index=i,
                    ),
                )
            )

        if not candidates:
            continue

        # One candidate boundary per joined type.
        candidates.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        out.append(candidates[0][1])

    return out


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def n_observations(counts: dict[str, int] | None) -> int:
    if not counts:
        return 0

    return sum(counts.get(x, 0) for x in TERMINALS)


def majority_terminal(
    counts: dict[str, int] | None,
) -> str | None:
    if not counts:
        return None

    # Same deterministic ordering used throughout the experiment.
    return max(
        TERMINALS,
        key=lambda x: counts.get(x, 0),
    )


@dataclass
class Evaluation:
    candidate_boundaries: int

    exact_n: int
    exact_correct: int

    stem_n: int
    stem_correct: int

    both_n: int
    both_exact_correct: int
    both_stem_correct: int


def evaluate(
    candidates: list[HiddenBoundary],
    model: VisibleBoundaryModel,
    *,
    min_exact_visible_examples: int = 3,
    min_stem_visible_examples: int = 3,
) -> Evaluation:

    exact_n = exact_correct = 0
    stem_n = stem_correct = 0

    both_n = 0
    both_exact_correct = 0
    both_stem_correct = 0

    for x in candidates:

        stem_c = model.stem_counts.get(x.stem)

        exact_c = (
            model.stem_next_counts
            .get(x.stem, {})
            .get(x.next_initial)
        )

        n_stem = n_observations(stem_c)
        n_exact = n_observations(exact_c)

        stem_pred = (
            majority_terminal(stem_c)
            if n_stem >= min_stem_visible_examples
            else None
        )

        exact_pred = (
            majority_terminal(exact_c)
            if n_exact >= min_exact_visible_examples
            else None
        )

        if exact_pred is not None:
            exact_n += 1
            exact_correct += int(
                exact_pred == x.terminal
            )

        if stem_pred is not None:
            stem_n += 1
            stem_correct += int(
                stem_pred == x.terminal
            )

        if (
            exact_pred is not None
            and stem_pred is not None
        ):
            both_n += 1

            both_exact_correct += int(
                exact_pred == x.terminal
            )

            both_stem_correct += int(
                stem_pred == x.terminal
            )

    return Evaluation(
        candidate_boundaries=len(candidates),

        exact_n=exact_n,
        exact_correct=exact_correct,

        stem_n=stem_n,
        stem_correct=stem_correct,

        both_n=both_n,
        both_exact_correct=both_exact_correct,
        both_stem_correct=both_stem_correct,
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def pct(a: int, b: int) -> float:
    return a / b if b else float("nan")


def print_report(
    ev: Evaluation,
    candidates: list[HiddenBoundary],
    model: VisibleBoundaryModel,
) -> None:

    print()
    print("=" * 72)
    print("VISIBLE → HIDDEN BOUNDARY TEST")
    print("=" * 72)

    print(
        f"\nCandidate joined internal boundaries: "
        f"{ev.candidate_boundaries:,}"
    )

    print("\n1. Stem + next-unit initial")
    print(
        f"   evaluable: {ev.exact_n:,}"
    )
    print(
        f"   correct:   {ev.exact_correct:,}"
    )
    print(
        f"   accuracy:  "
        f"{pct(ev.exact_correct, ev.exact_n):.3f}"
    )

    print("\n2. Stem only")
    print(
        f"   evaluable: {ev.stem_n:,}"
    )
    print(
        f"   correct:   {ev.stem_correct:,}"
    )
    print(
        f"   accuracy:  "
        f"{pct(ev.stem_correct, ev.stem_n):.3f}"
    )

    print("\n3. Same evaluable cases")
    print(
        f"   n:         {ev.both_n:,}"
    )
    print(
        "   stem + next initial: "
        f"{pct(ev.both_exact_correct, ev.both_n):.3f}"
    )
    print(
        "   stem only:           "
        f"{pct(ev.both_stem_correct, ev.both_n):.3f}"
    )

    improvement = (
        pct(ev.both_exact_correct, ev.both_n)
        - pct(ev.both_stem_correct, ev.both_n)
    )

    print(
        f"   improvement:          "
        f"{100 * improvement:+.1f} percentage points"
    )

    print()
    print("-" * 72)
    print("Illustrative candidates")
    print("-" * 72)

    shown = 0

    for x in candidates:

        exact = (
            model.stem_next_counts
            .get(x.stem, {})
            .get(x.next_initial)
        )

        stem = model.stem_counts.get(x.stem)

        if n_observations(exact) < 3:
            continue

        print(
            f"{x.joined:16s} -> "
            f"{x.left:10s} · {x.right:10s}   "
            f"terminal={x.terminal}"
        )

        print(
            f"    stem={x.stem!r}, "
            f"next_initial={x.next_initial!r}"
        )

        print(
            f"    visible stem+next counts = {exact}"
        )

        print(
            f"    prediction stem+next = "
            f"{majority_terminal(exact)!r}"
        )

        print(
            f"    prediction stem-only = "
            f"{majority_terminal(stem)!r}"
        )

        shown += 1

        if shown >= 15:
            break


# ---------------------------------------------------------------------------
# Optional JSON export
# ---------------------------------------------------------------------------

def export_json(
    output: Path,
    candidates: list[HiddenBoundary],
    model: VisibleBoundaryModel,
) -> None:

    rows = []

    for x in candidates:

        exact = (
            model.stem_next_counts
            .get(x.stem, {})
            .get(x.next_initial)
        )

        stem = model.stem_counts.get(x.stem)

        rows.append(
            {
                "joined": x.joined,
                "left": x.left,
                "right": x.right,

                "stem": x.stem,
                "observed_terminal": x.terminal,
                "next_initial": x.next_initial,

                "left_frequency": x.left_freq,
                "right_frequency": x.right_freq,

                "stem_counts": stem,
                "stem_next_counts": exact,

                "stem_prediction": (
                    majority_terminal(stem)
                    if n_observations(stem) >= 3
                    else None
                ),

                "stem_next_prediction": (
                    majority_terminal(exact)
                    if n_observations(exact) >= 3
                    else None
                ),
            }
        )

    output.write_text(
        json.dumps(
            rows,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "transcription",
        type=Path,
        help="Path to ZL3b-n.txt",
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Optional path for candidate-boundary JSON output",
    )

    args = parser.parse_args()

    lines = load_zl3b(args.transcription)

    print(
        f"Loaded {len(lines):,} body-text lines."
    )

    freq = corpus_frequencies(lines)

    print(
        f"Observed {sum(freq.values()):,} tokens "
        f"and {len(freq):,} surface types."
    )

    # ------------------------------------------------------------
    # IMPORTANT:
    # visible-boundary model is learned BEFORE looking at the
    # proposed internal boundary terminal.
    # ------------------------------------------------------------

    model = learn_from_visible_spaces(lines)

    candidates = infer_hidden_boundaries(
        freq,
        max_joined_frequency=2,
        min_joined_glyphs=6,
        min_component_frequency=5,
        min_component_glyphs=2,
    )

    ev = evaluate(
        candidates,
        model,
        min_exact_visible_examples=3,
        min_stem_visible_examples=3,
    )

    print_report(
        ev,
        candidates,
        model,
    )

    if args.json is not None:
        export_json(
            args.json,
            candidates,
            model,
        )

        print(
            f"\nWrote candidate details to "
            f"{args.json}"
        )


if __name__ == "__main__":
    main()
