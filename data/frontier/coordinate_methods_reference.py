#!/usr/bin/env python3
"""Reproduce the headline statistics and figures for the publication draft.

Usage:
    python3 analysis/reproduce_headlines.py /path/to/voynich-units

The data root must contain ZL3b.txt, the control-corpus directories, and
morphometry_voynichese/voynichese_boxes from the public reproducibility archive.
Only NumPy and Matplotlib are required beyond the Python standard library.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8.5,
    "axes.titlesize": "large",
    "axes.labelsize": "medium",
    "xtick.labelsize": "small",
    "ytick.labelsize": "small",
    "legend.fontsize": "small",
})
import numpy as np


SUBSTITUTIONS = [
    ("cth", "T"), ("ckh", "K"), ("cph", "P"), ("cfh", "F"),
    ("ch", "C"), ("sh", "S"), ("iin", "N"), ("in", "I"),
    ("ee", "E"),
]
BAD_BOUNDARY = set("?*<>{}[]()|@;:.,0123456789'")
BAD_ENTROPY = set("?*<>{}[]()|")
HEADER_RE = re.compile(r"^<(f[0-9]+[rv][0-9]*)>\s+<!\s*([^>]*)>")
LOCUS_RE = re.compile(r"^<(f[0-9rv]+[0-9]*)\.(\d+),([@+*=~])([A-Za-z])[^>]*>")

INK = "#202124"
BLUE = "#3977b9"
RED = "#d4514f"
PURPLE = "#6d4bd2"
GREY = "#8a8f98"


def collapse(token: str) -> str:
    for old, new in SUBSTITUTIONS:
        token = token.replace(old, new)
    return token


def clean_body(raw: str) -> str:
    text = raw[raw.index(">") + 1 :].strip()
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"\[([^:\]]*):[^\]]*\]", r"\1", text)
    return re.sub(r"\{[^}]*\}", "", text)


def valid_boundary_token(token: str) -> bool:
    return bool(token) and not (set(token) & BAD_BOUNDARY)


def parse_boundary_corpus(zl_path: Path) -> tuple[list[dict], list[tuple]]:
    metadata: dict[str, dict[str, str]] = {}
    lines: list[dict] = []
    with zl_path.open(encoding="utf-8", errors="replace") as stream:
        for raw in stream:
            header = HEADER_RE.match(raw)
            if header:
                metadata[header.group(1)] = dict(
                    re.findall(r"\$([A-Z])=([A-Za-z0-9]+)", header.group(2))
                )
                continue
            locus = LOCUS_RE.match(raw)
            if not locus or locus.group(4) != "P":
                continue
            page = locus.group(1)
            parts = re.split(r"([.,])", clean_body(raw))
            tokens = [collapse(parts[i].strip()) for i in range(0, len(parts), 2)]
            delimiters = [parts[i] for i in range(1, len(parts), 2)]
            if sum(valid_boundary_token(token) for token in tokens) < 4:
                continue
            meta = metadata.get(page, {})
            line = {
                "page": page,
                "marker": locus.group(3),
                "quire": meta.get("Q", "?"),
                "bifolio": (meta.get("Q", "?"), meta.get("B", "?")),
                "tokens": tokens,
                "delimiters": delimiters,
                "internal": [],
                "unigrams": [],
                "spaces": [],
            }
            for token in tokens:
                if not valid_boundary_token(token):
                    continue
                line["internal"].extend(zip(token, token[1:]))
                line["unigrams"].extend(token)
            for index, delimiter in enumerate(delimiters):
                if delimiter not in ".,":
                    continue
                left, right = tokens[index], tokens[index + 1]
                if not (valid_boundary_token(left) and valid_boundary_token(right)):
                    continue
                if index == 0:
                    position = "first"
                elif index == len(delimiters) - 1:
                    position = "last"
                else:
                    position = "mid"
                line["spaces"].append((delimiter, position, left[-1], right[0]))
            lines.append(line)

    linebreaks: list[tuple] = []
    for first, second in zip(lines, lines[1:]):
        if first["page"] != second["page"] or second["marker"] == "@":
            continue
        left = next(
            (token for token in reversed(first["tokens"]) if valid_boundary_token(token)),
            None,
        )
        right = next(
            (token for token in second["tokens"] if valid_boundary_token(token)),
            None,
        )
        if left and right:
            linebreaks.append((first["quire"], left[-1], right[0]))
    return lines, linebreaks


def association_scale(lines: list[dict]) -> dict:
    internal = [pair for line in lines for pair in line["internal"]]
    unigrams = [glyph for line in lines for glyph in line["unigrams"]]
    joint = Counter(internal)
    unigram = Counter(unigrams)
    vocabulary = sorted(unigram)
    index = {glyph: i for i, glyph in enumerate(vocabulary)}
    size = len(vocabulary)
    matrix = np.full((size, size), 0.5)
    for (left, right), count in joint.items():
        matrix[index[left], index[right]] += count
    matrix /= sum(joint.values()) + 0.5 * size * size
    marginal = np.array([unigram[glyph] for glyph in vocabulary], dtype=float)
    marginal /= marginal.sum()
    scores = np.log2(matrix / np.outer(marginal, marginal))
    internal_mean = float(np.mean([scores[index[a], index[b]] for a, b in internal]))
    random_mean = float(np.sum(np.outer(marginal, marginal) * scores))
    return {
        "scores": scores,
        "index": index,
        "internal_mean": internal_mean,
        "random_mean": random_mean,
        "denominator": internal_mean - random_mean,
    }


def pair_score(scale: dict, pair: tuple[str, str]) -> float:
    left, right = pair
    index = scale["index"]
    if left not in index or right not in index:
        return float("nan")
    return float(scale["scores"][index[left], index[right]])


def boundary_pools(lines: list[dict], linebreaks: list[tuple]) -> dict[str, list[tuple]]:
    spaces = [space for line in lines for space in line["spaces"]]
    return {
        "uncertain": [(a, b) for delimiter, _, a, b in spaces if delimiter == ","],
        "certain": [(a, b) for delimiter, _, a, b in spaces if delimiter == "."],
        "first": [(a, b) for _, position, a, b in spaces if position == "first"],
        "mid": [(a, b) for _, position, a, b in spaces if position == "mid"],
        "linebreak": [(a, b) for _, a, b in linebreaks],
    }


def boundary_index(lines: list[dict], linebreaks: list[tuple]) -> tuple[dict, dict]:
    scale = association_scale(lines)
    pools = boundary_pools(lines, linebreaks)
    result = {}
    for name, pairs in pools.items():
        values = np.array([pair_score(scale, pair) for pair in pairs])
        values = values[~np.isnan(values)]
        result[name] = (
            float((values.mean() - scale["random_mean"]) / scale["denominator"]),
            len(values),
        )
    return result, scale


def quire_bootstrap(
    lines: list[dict], linebreaks: list[tuple], repetitions: int, seed: int
) -> dict[str, tuple[float, float]]:
    by_quire: dict[str, list[dict]] = defaultdict(list)
    breaks_by_quire: dict[str, list[tuple]] = defaultdict(list)
    for line in lines:
        by_quire[line["quire"]].append(line)
    for quire, left, right in linebreaks:
        breaks_by_quire[quire].append((quire, left, right))
    quires = sorted(by_quire)
    rng = np.random.default_rng(seed)
    values = defaultdict(list)
    for _ in range(repetitions):
        selected = rng.choice(len(quires), len(quires), replace=True)
        sample_lines = [line for i in selected for line in by_quire[quires[i]]]
        sample_breaks = [item for i in selected for item in breaks_by_quire[quires[i]]]
        estimate, _ = boundary_index(sample_lines, sample_breaks)
        for name, (value, _) in estimate.items():
            values[name].append(value)
    return {
        name: tuple(np.percentile(series, [2.5, 97.5]))
        for name, series in values.items()
    }


def edge_null(scale: dict, pairs: list[tuple]) -> float:
    left = Counter(a for a, _ in pairs)
    right = Counter(b for _, b in pairs)
    total_left, total_right = sum(left.values()), sum(right.values())
    expectation = 0.0
    for a, left_count in left.items():
        for b, right_count in right.items():
            score = pair_score(scale, (a, b))
            if not math.isnan(score):
                expectation += (left_count / total_left) * (right_count / total_right) * score
    return (expectation - scale["random_mean"]) / scale["denominator"]


def design_effect(lines: list[dict], scale: dict, repetitions: int = 50000) -> tuple:
    aggregates = {"line": defaultdict(lambda: [0.0, 0]), "quire": defaultdict(lambda: [0.0, 0])}
    for line_number, line in enumerate(lines):
        values = []
        for _, _, left, right in line["spaces"]:
            score = pair_score(scale, (left, right))
            values.append((score - scale["random_mean"]) / scale["denominator"])
        for level, key in (("line", line_number), ("quire", line["quire"])):
            aggregates[level][key][0] += sum(values)
            aggregates[level][key][1] += len(values)
    rng = np.random.default_rng(20260807)
    standard_errors = {}
    for level in ("line", "quire"):
        array = np.array(list(aggregates[level].values()))
        clusters = len(array)
        estimates = []
        for _ in range(repetitions):
            sampled = array[rng.integers(0, clusters, clusters)].sum(axis=0)
            estimates.append(sampled[0] / sampled[1])
        standard_errors[level] = float(np.std(estimates))
    ratio = standard_errors["quire"] / standard_errors["line"]
    return standard_errors["line"], standard_errors["quire"], ratio, ratio * ratio


def two_sided_sign_p(positive: int, total: int) -> float:
    extreme = max(positive, total - positive)
    tail = sum(math.comb(total, value) for value in range(extreme, total + 1))
    return min(1.0, 2.0 * tail / (2 ** total))


def quire_robustness(lines: list[dict], linebreaks: list[tuple], scale: dict) -> dict:
    by_quire = defaultdict(lambda: {".": [], ",": []})
    for line in lines:
        for delimiter, _, left, right in line["spaces"]:
            score = pair_score(scale, (left, right))
            if math.isnan(score):
                continue
            value = (score - scale["random_mean"]) / scale["denominator"]
            by_quire[line["quire"]][delimiter].append(value)

    differences = []
    for values in by_quire.values():
        if values["."] and values[","]:
            differences.append(float(np.mean(values[","]) - np.mean(values["."])))

    quires = sorted({line["quire"] for line in lines})
    leave_one_out = []
    for omitted in quires:
        selected_lines = [line for line in lines if line["quire"] != omitted]
        selected_breaks = [item for item in linebreaks if item[0] != omitted]
        estimates, _ = boundary_index(selected_lines, selected_breaks)
        leave_one_out.append(estimates["uncertain"][0] - estimates["certain"][0])

    positive = sum(value > 0 for value in differences)
    return {
        "quires": len(differences),
        "positive": positive,
        "sign_p": two_sided_sign_p(positive, len(differences)),
        "fixed_range": (min(differences), max(differences)),
        "fixed_median": float(np.median(differences)),
        "leave_one_out_range": (min(leave_one_out), max(leave_one_out)),
        "leave_one_out_median": float(np.median(leave_one_out)),
    }


def vy_tokens(box_path: Path) -> list[dict]:
    data = json.loads(box_path.read_text())
    vocabulary = [item[0] for item in data[0]]
    tokens = []
    line = 0
    previous_x = None
    for entry in data[1]:
        token = {
            "word": vocabulary[entry[0]],
            "x": entry[1], "y": entry[2], "w": entry[3], "h": entry[4],
        }
        if previous_x is not None and token["x"] < previous_x - 3:
            line += 1
        token["line"] = line
        previous_x = token["x"]
        tokens.append(token)
    return tokens


def zl_folio_tokens(zl_path: Path, folio: str) -> tuple[list[str], list[str]]:
    pattern = re.compile(r"^<" + re.escape(folio) + r"\.(\d+),([@+*=~])([A-Za-z])")
    bad = set("?*<>{}[]()|")
    tokens, separators = [], []
    with zl_path.open(encoding="utf-8", errors="replace") as stream:
        for raw in stream:
            match = pattern.match(raw)
            if not match or match.group(3) != "P":
                continue
            current, line_tokens, line_separators = "", [], []
            for character in clean_body(raw):
                if character in ".,":
                    if current and not (set(current) & bad):
                        line_tokens.append(current)
                        line_separators.append(character)
                    current = ""
                else:
                    current += character
            if current and not (set(current) & bad):
                line_tokens.append(current)
            line_separators = line_separators[: len(line_tokens) - 1]
            for index, token in enumerate(line_tokens):
                tokens.append(token)
                separators.append(
                    line_separators[index] if index < len(line_separators) else "L"
                )
    return tokens, separators


def coordinate_rows(data_root: Path, scale: dict) -> tuple[list[dict], int, int]:
    box_directory = data_root / "morphometry_voynichese" / "voynichese_boxes"
    rows = []
    aligned = 0
    total = 0
    for box_path in sorted(box_directory.glob("*.js")):
        folio = box_path.stem
        visual = vy_tokens(box_path)
        textual, separators = zl_folio_tokens(data_root / "ZL3b.txt", folio)
        if not textual:
            continue
        total += len(visual)
        median_width = np.median([token["w"] for token in visual]) or 1.0
        matcher = SequenceMatcher(
            a=[collapse(token["word"]) for token in visual],
            b=[collapse(token) for token in textual],
            autojunk=False,
        )
        for visual_start, text_start, length in matcher.get_matching_blocks():
            aligned += length
            for offset in range(length - 1):
                left = visual[visual_start + offset]
                right = visual[visual_start + offset + 1]
                if left["line"] != right["line"]:
                    continue
                label = separators[text_start + offset]
                if label not in ".,":
                    continue
                pair = (collapse(left["word"])[-1], collapse(right["word"])[0])
                raw_score = pair_score(scale, pair)
                normalized_score = (
                    (raw_score - scale["random_mean"]) / scale["denominator"]
                )
                rows.append({
                    "gap": (right["x"] - (left["x"] + left["w"])) / median_width,
                    "label": label,
                    "pair": pair,
                    "folio": folio,
                    "score": normalized_score,
                })
    return rows, aligned, total


def transcription_tokens_and_separators(
    body: str, bad: set[str]
) -> tuple[list[str], list[str]]:
    """Extract clean tokens and the separators between retained tokens."""
    body = re.sub(r"<[^>]*>", "", body)
    body = re.sub(r"\[([^:\]]*):[^\]]*\]", r"\1", body)
    body = re.sub(r"\{[^}]*\}", "", body).rstrip("-=").strip()
    tokens, separators, current = [], [], ""
    for character in body:
        if character in ".,":
            if current and not (set(current) & bad):
                tokens.append(current)
                separators.append(character)
            current = ""
        else:
            current += character
    if current and not (set(current) & bad):
        tokens.append(current)
    return tokens, separators[: max(0, len(tokens) - 1)]


def parse_zl_separator_lines(zl_path: Path) -> dict[str, list[tuple[int, list[str], list[str]]]]:
    pattern = re.compile(r"^<(f[0-9]+[rv][0-9]?)\.(\d+),([@+*=~])([A-Za-z])")
    bad = set("?*<>{}[]()|")
    output = defaultdict(list)
    with zl_path.open(encoding="utf-8", errors="replace") as stream:
        for raw in stream:
            match = pattern.match(raw)
            if not match or match.group(4) != "P":
                continue
            tokens, separators = transcription_tokens_and_separators(
                raw[raw.index(">") + 1 :], bad
            )
            if tokens:
                output[match.group(1)].append((int(match.group(2)), tokens, separators))
    return dict(output)


def parse_v101_separator_lines(v101_path: Path) -> dict[str, dict[int, list[str]]]:
    pattern = re.compile(r"^<([0-9]+[rv][0-9]?)\.(\d+)>")
    bad = set("?*<>{}[]()|!%&")
    output = defaultdict(dict)
    with v101_path.open(encoding="utf-8", errors="replace") as stream:
        for raw in stream:
            match = pattern.match(raw)
            if not match:
                continue
            tokens, separators = transcription_tokens_and_separators(
                raw[raw.index(">") + 1 :], bad
            )
            if tokens:
                output["f" + match.group(1)][int(match.group(2))] = separators
    return {folio: dict(lines) for folio, lines in output.items()}


def second_transcription_check(data_root: Path, v101_path: Path) -> dict:
    """Compare ZL and v101 weak-space marks and test a gap dose response."""
    zl = parse_zl_separator_lines(data_root / "ZL3b.txt")
    v101 = parse_v101_separator_lines(v101_path)
    counts = {"both_uncertain": 0, "zl_only": 0, "v101_only": 0, "neither": 0}
    comparable_lines = 0
    for folio, lines in zl.items():
        for line_number, _, zl_separators in lines:
            other = v101.get(folio, {}).get(line_number)
            if other is None or len(other) != len(zl_separators):
                continue
            comparable_lines += 1
            for first, second in zip(zl_separators, other):
                if first == "," and second == ",":
                    counts["both_uncertain"] += 1
                elif first == ",":
                    counts["zl_only"] += 1
                elif second == ",":
                    counts["v101_only"] += 1
                else:
                    counts["neither"] += 1
    total = sum(counts.values())
    observed = (counts["both_uncertain"] + counts["neither"]) / total
    zl_rate = (counts["both_uncertain"] + counts["zl_only"]) / total
    v101_rate = (counts["both_uncertain"] + counts["v101_only"]) / total
    expected = zl_rate * v101_rate + (1 - zl_rate) * (1 - v101_rate)

    gaps_by_vote = {0: [], 1: [], 2: []}
    box_directory = data_root / "morphometry_voynichese" / "voynichese_boxes"
    for box_path in sorted(box_directory.glob("*.js")):
        folio = box_path.stem
        if folio not in zl:
            continue
        visual = vy_tokens(box_path)
        median_width = np.median([token["w"] for token in visual]) or 1.0
        visual_lines = defaultdict(list)
        for token in visual:
            visual_lines[token["line"]].append(token)
        keys = sorted(visual_lines)
        for line_index, (line_number, zl_tokens, zl_separators) in enumerate(zl[folio]):
            if line_index >= len(keys):
                continue
            other = v101.get(folio, {}).get(line_number)
            if other is None or len(other) != len(zl_separators):
                continue
            line = visual_lines[keys[line_index]]
            matcher = SequenceMatcher(
                a=[collapse(token["word"]) for token in line],
                b=[collapse(token) for token in zl_tokens],
                autojunk=False,
            )
            for visual_start, text_start, length in matcher.get_matching_blocks():
                for offset in range(length - 1):
                    separator_index = text_start + offset
                    if separator_index >= len(zl_separators):
                        continue
                    left = line[visual_start + offset]
                    right = line[visual_start + offset + 1]
                    votes = int(zl_separators[separator_index] == ",") + int(
                        other[separator_index] == ","
                    )
                    gaps_by_vote[votes].append(
                        (right["x"] - (left["x"] + left["w"])) / median_width
                    )
    return {
        "comparable_lines": comparable_lines,
        "comparable_boundaries": total,
        **counts,
        "zl_uncertain_rate": zl_rate,
        "v101_uncertain_rate": v101_rate,
        "raw_agreement": observed,
        "cohen_kappa": (observed - expected) / (1 - expected),
        "gap_by_uncertain_votes": {
            str(votes): {
                "n": len(values),
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
            }
            for votes, values in gaps_by_vote.items()
        },
    }


def demean(values: np.ndarray, codes: np.ndarray, groups: int) -> np.ndarray:
    sums = np.bincount(codes, weights=values, minlength=groups)
    counts = np.bincount(codes, minlength=groups)
    return values - (sums / np.maximum(counts, 1))[codes]


def rank_auc(certain: list[float] | np.ndarray,
             uncertain: list[float] | np.ndarray) -> float:
    """Probability that a random certain gap exceeds a random uncertain gap."""
    certain = np.asarray(certain)
    uncertain = np.sort(np.asarray(uncertain))
    lower = np.searchsorted(uncertain, certain, side="left")
    upper = np.searchsorted(uncertain, certain, side="right")
    return float(np.sum(lower + 0.5 * (upper - lower)) /
                 (len(certain) * len(uncertain)))


def best_gap_threshold(rows: list[dict]) -> tuple[float, float]:
    values = np.array([row["gap"] for row in rows])
    uncertain = np.array([row["label"] == "," for row in rows])
    order = np.argsort(values, kind="stable")
    values, uncertain = values[order], uncertain[order]
    true_positive = np.cumsum(uncertain)
    false_positive = np.cumsum(~uncertain)
    positives, negatives = uncertain.sum(), (~uncertain).sum()
    # Evaluate only attainable thresholds, after the final member of each tie.
    candidates = np.r_[np.flatnonzero(values[:-1] < values[1:]), len(values) - 1]
    balanced = 0.5 * (
        true_positive[candidates] / positives
        + (negatives - false_positive[candidates]) / negatives
    )
    best = int(candidates[np.argmax(balanced)])
    return float(values[best]), float(np.max(balanced))


def leave_one_folio_out_classifier(
    by_folio: dict[str, list[dict]], folios: list[str]
) -> dict:
    true_positive = false_positive = true_negative = false_negative = 0
    for held_out in folios:
        training = [
            row for folio in folios if folio != held_out for row in by_folio[folio]
        ]
        threshold, _ = best_gap_threshold(training)
        for row in by_folio[held_out]:
            predicted = row["gap"] <= threshold
            actual = row["label"] == ","
            if predicted and actual:
                true_positive += 1
            elif predicted:
                false_positive += 1
            elif actual:
                false_negative += 1
            else:
                true_negative += 1
    sensitivity = true_positive / (true_positive + false_negative)
    specificity = true_negative / (true_negative + false_positive)
    return {
        "sensitivity": sensitivity,
        "specificity": specificity,
        "balanced_accuracy": 0.5 * (sensitivity + specificity),
    }


def two_way_fixed_effect(rows: list[dict]) -> float:
    gaps = np.array([row["gap"] for row in rows])
    uncertain = np.array([row["label"] == "," for row in rows], dtype=float)
    pairs = {pair: index for index, pair in enumerate(sorted({row["pair"] for row in rows}))}
    folios = {folio: index for index, folio in enumerate(sorted({row["folio"] for row in rows}))}
    pair_codes = np.array([pairs[row["pair"]] for row in rows])
    folio_codes = np.array([folios[row["folio"]] for row in rows])

    def residualize(values: np.ndarray) -> np.ndarray:
        values = values - values.mean()
        for _ in range(1000):
            previous = values.copy()
            values = demean(values, pair_codes, len(pairs))
            values = demean(values, folio_codes, len(folios))
            if np.max(np.abs(values - previous)) < 1e-12:
                break
        return values

    residual_gap = residualize(gaps)
    residual_uncertain = residualize(uncertain)
    return float(
        np.sum(residual_uncertain * residual_gap)
        / np.sum(residual_uncertain * residual_uncertain)
    )


def pair_fixed_effect(rows: list[dict]) -> float:
    gaps = np.array([row["gap"] for row in rows])
    uncertain = np.array([row["label"] == "," for row in rows], dtype=float)
    pairs = {pair: index for index, pair in enumerate(sorted({row["pair"] for row in rows}))}
    codes = np.array([pairs[row["pair"]] for row in rows])
    gaps = demean(gaps, codes, len(pairs))
    uncertain = demean(uncertain, codes, len(pairs))
    return float(np.sum(uncertain * gaps) / np.sum(uncertain * uncertain))


def coordinate_statistics(rows: list[dict], repetitions: int) -> dict:
    certain = np.array([row["gap"] for row in rows if row["label"] == "."])
    uncertain = np.array([row["gap"] for row in rows if row["label"] == ","])
    folios = sorted({row["folio"] for row in rows})
    by_folio = defaultdict(list)
    for row in rows:
        by_folio[row["folio"]].append(row)
    rng = np.random.default_rng(7)
    differences = []
    coefficients = []
    aucs = []
    rng_fe = np.random.default_rng(11)
    for _ in range(repetitions):
        sample = rng.choice(folios, len(folios), replace=True)
        selected = [row for folio in sample for row in by_folio[folio]]
        c = [row["gap"] for row in selected if row["label"] == "."]
        u = [row["gap"] for row in selected if row["label"] == ","]
        differences.append(float(np.mean(c) - np.mean(u)))
        aucs.append(rank_auc(c, u))
        sample_fe = rng_fe.choice(folios, len(folios), replace=True)
        selected_fe = [row for folio in sample_fe for row in by_folio[folio]]
        coefficients.append(pair_fixed_effect(selected_fe))
    paired_folios = [
        folio for folio in folios
        if {row["label"] for row in by_folio[folio]} == {".", ","}
    ]
    positive = 0
    for folio in paired_folios:
        group = by_folio[folio]
        c = np.mean([row["gap"] for row in group if row["label"] == "."])
        u = np.mean([row["gap"] for row in group if row["label"] == ","])
        positive += c > u
    pair_groups = defaultdict(lambda: {".": [], ",": []})
    for row in rows:
        pair_groups[row["pair"]][row["label"]].append(row["gap"])
    common_pairs = [
        pair for pair, values in pair_groups.items()
        if len(values["."]) >= 5 and len(values[","]) >= 5
    ]
    return {
        "certain": certain,
        "uncertain": uncertain,
        "difference": float(certain.mean() - uncertain.mean()),
        "difference_ci": tuple(np.percentile(differences, [2.5, 97.5])),
        "pair_fe": pair_fixed_effect(rows),
        "pair_fe_ci": tuple(np.percentile(coefficients, [2.5, 97.5])),
        "folios": len(folios),
        "paired_folios": len(paired_folios),
        "positive_folios": positive,
        "common_pairs": len(common_pairs),
        "positive_pairs": sum(
            np.mean(pair_groups[pair]["."]) > np.mean(pair_groups[pair][","])
            for pair in common_pairs
        ),
        "auc": rank_auc(certain, uncertain),
        "auc_ci": tuple(np.percentile(aucs, [2.5, 97.5])),
        "two_way_fe": two_way_fixed_effect(rows),
        "threshold": best_gap_threshold(rows),
        "leave_one_out": leave_one_folio_out_classifier(by_folio, folios),
        "correlation": float(np.corrcoef(
            [row["gap"] for row in rows], [row["score"] for row in rows]
        )[0, 1]),
        "pair_groups": pair_groups,
        "common_pair_names": common_pairs,
    }


def entropy(sequence: list[str]) -> float:
    counts = Counter(sequence)
    total = len(sequence)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def conditional_entropy(sequence: list[str]) -> float:
    bigrams = Counter(zip(sequence, sequence[1:]))
    left = Counter()
    for (current, _), count in bigrams.items():
        left[current] += count
    total = sum(bigrams.values())
    return -sum(
        (count / total) * math.log2(count / left[current])
        for (current, _), count in bigrams.items()
    )


def within_token_conditional_entropy(words: list[str]) -> float:
    bigrams = Counter(pair for word in words for pair in zip(word, word[1:]))
    left = Counter()
    for (current, _), count in bigrams.items():
        left[current] += count
    total = sum(bigrams.values())
    return -sum(
        (count / total) * math.log2(count / left[current])
        for (current, _), count in bigrams.items()
    )


def load_tess(paths: list[str]) -> list[str]:
    output = []
    for path in paths:
        with open(path, encoding="utf-8", errors="replace") as stream:
            for line in stream:
                line = re.sub(r"^<[^>]*>", "", line)
                line = re.sub(r"[^A-Za-zÀ-ÿ ]", " ", line)
                output.extend(word.lower() for word in line.split() if word.isalpha())
    return output


def load_gutenberg(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    start, end = text.find("*** START"), text.find("*** END")
    if start > 0:
        text = text[text.find("\n", start) :]
    if end > 0:
        text = text[:end]
    text = re.sub(r"[^A-Za-zÀ-ÿ ]", " ", text)
    return [word.lower() for word in text.split() if word.isalpha()]


def entropy_word_corpora(data_root: Path) -> dict[str, list[str]]:
    raw_tokens = []
    with (data_root / "ZL3b.txt").open(encoding="utf-8", errors="replace") as stream:
        for raw in stream:
            match = LOCUS_RE.match(raw)
            if not match or match.group(4) != "P":
                continue
            raw_tokens.extend(
                word for word in re.split(r"[.,]", clean_body(raw))
                if word and not (set(word) & BAD_ENTROPY)
            )
    return {
        "Voynichese, composite-collapsed EVA": [collapse(word) for word in raw_tokens],
        "Voynichese, decomposed EVA": raw_tokens,
        "Pliny, botanical Latin": load_tess(sorted(glob.glob(str(data_root / "herbal/pliny*.tess")))),
        "Celsus and Caesar, Latin": load_tess(sorted(glob.glob(str(data_root / "latin/*.tess")))),
        "Culpeper, English herbal": load_gutenberg(data_root / "herbal/culpeper_en.txt"),
        "Italian prose": (
            load_gutenberg(data_root / "italian/27608.txt")
            + load_gutenberg(data_root / "italian/26166.txt")
        ),
    }


def entropy_corpora(corpora: dict[str, list[str]]) -> list[tuple]:
    primary = corpora["Voynichese, composite-collapsed EVA"]
    sample_size = len(primary)
    character_sample = sum(len(word) for word in primary)
    rows = []
    for name, words in corpora.items():
        words = words[:sample_size]
        symbols = [symbol for word in words for symbol in word]
        rows.append((
            name,
            entropy(symbols),
            conditional_entropy(symbols),
            entropy(words),
            within_token_conditional_entropy(words),
            conditional_entropy(symbols[:character_sample]),
        ))
    return rows


def entropy_window_robustness(
    corpora: dict[str, list[str]], repetitions: int, seed: int
) -> dict[str, tuple[float, float, float]]:
    target = "".join(corpora["Voynichese, composite-collapsed EVA"])
    target_length = len(target)
    rng = np.random.default_rng(seed)
    result = {}
    for name, words in corpora.items():
        if name.startswith("Voynichese"):
            continue
        sequence = "".join(words)
        starts = rng.integers(0, len(sequence) - target_length + 1, repetitions)
        values = [
            conditional_entropy(sequence[start : start + target_length])
            for start in starts
        ]
        result[name] = (
            float(min(values)),
            float(np.median(values)),
            float(max(values)),
        )
    return result


def make_boundary_coordinate_figure(output, estimates, intervals, nulls, rows, stats):
    fig = plt.figure(figsize=(7.5, 8.5))
    grid = fig.add_gridspec(
        3, 2, height_ratios=[0.85, 1.15, 0.85],
        hspace=0.62, wspace=0.30,
        left=0.125, right=0.975, top=0.965, bottom=0.055,
    )
    axA = fig.add_subplot(grid[0, :])
    axB = fig.add_subplot(grid[1, 0])
    axC = fig.add_subplot(grid[1, 1])
    axD = fig.add_subplot(grid[2, :])

    # --- A: boundary association ---
    names = ["within-token\npair", "uncertain\nseparator", "first separator\nof line",
             "mid-line\nseparator", "certain\nseparator", "line break"]
    keys = [None, "uncertain", "first", "mid", "certain", "linebreak"]
    values = [1.0] + [estimates[key][0] for key in keys[1:]]
    lower = [0.0] + [values[i] - intervals[keys[i]][0] for i in range(1, len(keys))]
    upper = [0.0] + [intervals[keys[i]][1] - values[i] for i in range(1, len(keys))]
    x = np.arange(len(names))
    axA.axhline(0, color=GREY, linewidth=0.9, linestyle="--")
    axA.errorbar(x, values, yerr=[lower, upper], fmt="o", color=INK,
                 ecolor=INK, capsize=3, markersize=6, label="observed")
    axA.scatter(x[1:], [nulls[key] for key in keys[1:]], facecolors="white",
                edgecolors=RED, linewidth=1.3, s=38, label="edge-composition null")
    axA.set_xticks(x, names)
    axA.set_xlabel("boundary class")
    axA.set_ylabel("normalised internality index  $I$")
    axA.set_ylim(-0.14, 1.08)
    axA.set_title("A  Boundary association by transcription certainty and position",
                  loc="left", fontweight="bold")
    axA.legend(frameon=False, ncol=2, loc="upper right")

    # --- B: bounding-box gap histogram ---
    certain = stats["certain"]
    uncertain = stats["uncertain"]
    bins = np.linspace(-0.12, 0.42, 55)
    axB.hist(certain, bins=bins, density=True, color=BLUE, alpha=0.68,
             label=f"certain (n={len(certain):,})")
    axB.hist(uncertain, bins=bins, density=True, color=RED, alpha=0.58,
             label=f"uncertain (n={len(uncertain):,})")
    axB.axvline(np.median(certain), color=BLUE, linestyle="--", linewidth=1)
    axB.axvline(np.median(uncertain), color=RED, linestyle="--", linewidth=1)
    axB.set_title("B  Bounding-box gap by ZL label", loc="left", fontweight="bold")
    axB.set_xlabel("box gap (fraction of folio median token width)")
    axB.set_ylabel("density")
    axB.legend(frameon=False, fontsize="small")

    # --- C: same flanking glyph pair ---
    pair_groups = stats["pair_groups"]
    common = sorted(
        stats["common_pair_names"],
        key=lambda pair: -(len(pair_groups[pair]["."]) + len(pair_groups[pair][","])),
    )[:12]
    y = np.arange(len(common))[::-1]
    certain_means = [np.mean(pair_groups[pair]["."]) for pair in common]
    uncertain_means = [np.mean(pair_groups[pair][","]) for pair in common]
    for yi, c, u in zip(y, certain_means, uncertain_means):
        axC.plot([u, c], [yi, yi], color=GREY, linewidth=1)
    axC.scatter(certain_means, y, color=BLUE, s=26)
    axC.scatter(uncertain_means, y, color=RED, s=26)
    axC.set_yticks(y, [f"{a}\u2192{b}" for a, b in common])
    axC.set_xlabel("mean normalised box gap")
    axC.set_title("C  Same flanking glyph pair", loc="left", fontweight="bold")

    # --- D: association vs box gap ---
    scores = np.array([row["score"] for row in rows])
    gaps = np.array([row["gap"] for row in rows])
    centers, means, errors = [], [], []
    rng = np.random.default_rng(19)
    folios = sorted({row["folio"] for row in rows})
    order = np.argsort(scores)
    chunks = np.array_split(order, 10)
    for chunk in chunks:
        centers.append(float(np.mean(scores[chunk])))
        means.append(float(np.mean(gaps[chunk])))
        chunk_by_folio = defaultdict(list)
        for index in chunk:
            chunk_by_folio[rows[index]["folio"]].append(rows[index]["gap"])
        boot = []
        for _ in range(400):
            sample = rng.choice(folios, len(folios), replace=True)
            selected = [gap for folio in sample for gap in chunk_by_folio.get(folio, [])]
            if selected:
                boot.append(np.mean(selected))
        errors.append(np.std(boot))
    axD.errorbar(centers, means, yerr=errors, color=PURPLE, marker="o",
                 linewidth=1.3, markersize=4, capsize=3)
    axD.set_xlabel("transcription-only boundary association score")
    axD.set_ylabel("mean normalised box gap")
    axD.set_title(
        f"D  Boundary association and bounding-box gap  ($r={stats['correlation']:.2f}$)",
        loc="left", fontweight="bold",
    )

    for ax in (axA, axB, axC, axD):
        ax.spines[["top", "right"]].set_visible(False)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=240, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_root", type=Path)
    parser.add_argument("--bootstrap", type=int, default=1500)
    parser.add_argument("--entropy-windows", type=int, default=300)
    parser.add_argument("--output", type=Path, default=Path("figures"))
    parser.add_argument(
        "--v101", type=Path,
        help="optional Glen Claston v101 transcription for a second-reader space check",
    )
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    root = args.data_root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    lines, linebreaks = parse_boundary_corpus(root / "ZL3b.txt")
    estimates, scale = boundary_index(lines, linebreaks)
    intervals = quire_bootstrap(lines, linebreaks, args.bootstrap, 20260808)
    pools = boundary_pools(lines, linebreaks)
    nulls = {name: edge_null(scale, pairs) for name, pairs in pools.items()}
    line_se, quire_se, se_ratio, variance_ratio = design_effect(lines, scale)
    quire = quire_robustness(lines, linebreaks, scale)

    rows, aligned, total = coordinate_rows(root, scale)
    coordinate = coordinate_statistics(rows, args.bootstrap)
    entropy_words = entropy_word_corpora(root)
    entropy_rows = entropy_corpora(entropy_words)
    entropy_windows = entropy_window_robustness(
        entropy_words, args.entropy_windows, 20260810
    )
    second_transcription = (
        second_transcription_check(root, args.v101.resolve()) if args.v101 else None
    )

    make_boundary_coordinate_figure(
        output / "F1_boundary_coordinate_publication.png",
        estimates, intervals, nulls, rows, coordinate)

    if args.json_output:
        result = {
            "boundary": {
                name: {
                    "index": estimates[name][0], "n": estimates[name][1],
                    "ci": intervals[name], "edge_null": nulls[name],
                }
                for name in estimates
            },
            "coordinate": {
                "aligned_tokens": aligned, "visual_tokens": total,
                "boundaries": len(rows), "difference": coordinate["difference"],
                "difference_ci": coordinate["difference_ci"],
                "pair_fixed_effect": coordinate["pair_fe"],
                "pair_fixed_effect_ci": coordinate["pair_fe_ci"],
                "auc": coordinate["auc"], "auc_ci": coordinate["auc_ci"],
                "leave_one_folio_out": coordinate["leave_one_out"],
            },
            "entropy": [
                {
                    "corpus": name, "marginal": h1, "conditional": h2,
                    "token_entropy": token_h, "within_token_conditional": within_h2,
                    "matched_character_conditional": matched_h2,
                }
                for name, h1, h2, token_h, within_h2, matched_h2 in entropy_rows
            ],
            "second_transcription": second_transcription,
        }
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2) + "\n")

    print("BOUNDARY CORPUS")
    print(f"lines={len(lines)} pages={len({line['page'] for line in lines})} "
          f"bifolios={len({line['bifolio'] for line in lines})} "
          f"quires={len({line['quire'] for line in lines})}")
    for name in ("uncertain", "first", "mid", "certain", "linebreak"):
        value, count = estimates[name]
        low, high = intervals[name]
        print(f"{name:10s} I={value:.3f} [{low:.3f}, {high:.3f}] n={count} "
              f"edge_null={nulls[name]:+.3f}")
    print(f"design SE line={line_se:.5f} quire={quire_se:.5f} "
          f"ratio={se_ratio:.2f} variance_ratio={variance_ratio:.1f}")
    print(f"quire contrast positive={quire['positive']}/{quire['quires']} "
          f"sign_p={quire['sign_p']:.3g} "
          f"fixed_range=[{quire['fixed_range'][0]:.3f}, {quire['fixed_range'][1]:.3f}] "
          f"median={quire['fixed_median']:.3f}")
    print(f"leave-one-quire-out contrast "
          f"range=[{quire['leave_one_out_range'][0]:.3f}, "
          f"{quire['leave_one_out_range'][1]:.3f}] "
          f"median={quire['leave_one_out_median']:.3f}")

    print("\nCOORDINATE VALIDATION")
    print(f"aligned={aligned}/{total} ({aligned/total:.1%}) boundaries={len(rows)}")
    print(f"certain n={len(coordinate['certain'])} mean={coordinate['certain'].mean():.4f} "
          f"median={np.median(coordinate['certain']):.4f}")
    print(f"uncertain n={len(coordinate['uncertain'])} mean={coordinate['uncertain'].mean():.4f} "
          f"median={np.median(coordinate['uncertain']):.4f}")
    print(f"difference={coordinate['difference']:+.4f} "
          f"CI=[{coordinate['difference_ci'][0]:+.4f}, {coordinate['difference_ci'][1]:+.4f}]")
    print(f"pair_FE={coordinate['pair_fe']:+.4f} "
          f"CI=[{coordinate['pair_fe_ci'][0]:+.4f}, {coordinate['pair_fe_ci'][1]:+.4f}]")
    print(f"pair+folio_FE={coordinate['two_way_fe']:+.4f}")
    print(f"folios={coordinate['folios']} positive={coordinate['positive_folios']}/"
          f"{coordinate['paired_folios']} common_pairs={coordinate['positive_pairs']}/"
          f"{coordinate['common_pairs']} correlation={coordinate['correlation']:+.3f}")
    print(f"gap_AUC={coordinate['auc']:.4f} "
          f"CI=[{coordinate['auc_ci'][0]:.4f}, {coordinate['auc_ci'][1]:.4f}] "
          f"full_threshold={coordinate['threshold'][0]:.4f} "
          f"balanced_accuracy={coordinate['threshold'][1]:.4f}")
    leave_out = coordinate["leave_one_out"]
    print(f"leave-one-folio-out sensitivity={leave_out['sensitivity']:.4f} "
          f"specificity={leave_out['specificity']:.4f} "
          f"balanced_accuracy={leave_out['balanced_accuracy']:.4f}")

    print("\nENTROPY")
    for name, h1, h2, token_h, within_h2, matched_h2 in entropy_rows:
        print(f"{name:28s} H1={h1:.2f} H(next|current)={h2:.2f} "
              f"choices={2 ** h2:.2f} H(within-token)={within_h2:.2f} "
              f"H(char-matched)={matched_h2:.2f} H(token)={token_h:.2f}")
    print(f"contiguous control windows={args.entropy_windows} per corpus, "
          "Voynich collapsed characters="
          f"{sum(len(word) for word in entropy_words['Voynichese, composite-collapsed EVA'])}, "
          "decomposed characters="
          f"{sum(len(word) for word in entropy_words['Voynichese, decomposed EVA'])}")
    for name, (minimum, median, maximum) in entropy_windows.items():
        print(f"{name:28s} min={minimum:.3f} median={median:.3f} max={maximum:.3f}")

    if second_transcription:
        print("\nSECOND-TRANSCRIPTION SPACE CHECK")
        print(
            f"lines={second_transcription['comparable_lines']} "
            f"boundaries={second_transcription['comparable_boundaries']} "
            f"raw_agreement={second_transcription['raw_agreement']:.3f} "
            f"kappa={second_transcription['cohen_kappa']:.3f}"
        )
        print(
            f"both={second_transcription['both_uncertain']} "
            f"ZL-only={second_transcription['zl_only']} "
            f"v101-only={second_transcription['v101_only']} "
            f"neither={second_transcription['neither']}"
        )
        for votes, values in second_transcription["gap_by_uncertain_votes"].items():
            print(
                f"uncertain votes={votes}: n={values['n']} "
                f"mean_gap={values['mean']:.4f} median_gap={values['median']:.4f}"
            )


if __name__ == "__main__":
    main()
