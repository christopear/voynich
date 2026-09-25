from __future__ import annotations

import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

EVA_COMPOUNDS = ("cth", "ckh", "cph", "cfh", "ch", "sh")
TERMINALS = ("n", "l", "r")
BOUNDARY_TERMINALS = ("n", "l", "r", "m")


@dataclass
class Page:
    page_id: str
    meta: dict[str, str] = field(default_factory=dict)
    comments: list[str] = field(default_factory=list)


@dataclass
class TextLine:
    page: str
    locus: str
    descriptor: str
    is_paragraph_start: bool
    tokens: list[str]


def eva_glyphs(word: str) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(word):
        hit = next((c for c in EVA_COMPOUNDS if word.startswith(c, i)), None)
        if hit:
            out.append(hit)
            i += len(hit)
        else:
            out.append(word[i])
            i += 1
    return out


def tokenise_ivtff_body(s: str) -> list[str]:
    """Conservative tokeniser used in the exploratory analysis."""
    s = s.replace("<->", " ")
    s = re.sub(r"<!.*?>", " ", s)
    s = s.replace("<%>", " ").replace("<$>", " ").replace("<~>", " ")
    s = re.sub(r"\[([a-z']+):[^\]]+\]", r"\1", s, flags=re.I)
    s = re.sub(r"\{([^}]*)\}", r"\1", s)
    s = re.sub(r"@\d+;", " ", s)
    s = s.replace("?", "").replace("'", "").replace("’", "")
    parts = re.split(r"[.,\s=<>-]+", s.lower())
    out = []
    for x in parts:
        x = re.sub(r"[^a-z]", "", x)
        if x:
            out.append(x)
    return out


def parse_zl3b(path: str | Path) -> tuple[dict[str, Page], list[TextLine]]:
    pages: dict[str, Page] = {}
    lines: list[TextLine] = []
    current_page: str | None = None
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            hm = re.match(r"^<(f[^.>\s]+)>\s*<!([^>]*)>", line)
            if hm:
                current_page = hm.group(1)
                p = pages.setdefault(current_page, Page(current_page))
                for m in re.finditer(r"\$(\w)=([^\s>]+)", hm.group(2)):
                    p.meta[m.group(1)] = m.group(2)
                continue
            if line.startswith("#"):
                if current_page:
                    pages.setdefault(current_page, Page(current_page)).comments.append(
                        re.sub(r"^#\s?", "", line)
                    )
                continue
            lm = re.match(r"^<(f[^.>]+\.\d+),([^>]*)>\s*(.*)$", line)
            if not lm or "P" not in lm.group(2):
                continue
            page = lm.group(1).split(".")[0]
            tokens = tokenise_ivtff_body(lm.group(3))
            if tokens:
                lines.append(
                    TextLine(
                        page=page,
                        locus=lm.group(1),
                        descriptor=lm.group(2),
                        is_paragraph_start="<%>" in lm.group(3),
                        tokens=tokens,
                    )
                )
    return pages, lines


def select_pages(
    pages: dict[str, Page],
    *,
    section: str | None = None,
    currier: str | None = None,
    hand: str | None = None,
) -> list[str]:
    out = []
    for pid, p in pages.items():
        if section is not None and p.meta.get("I") != section:
            continue
        if currier is not None and p.meta.get("L") != currier:
            continue
        if hand is not None and p.meta.get("H") != hand:
            continue
        out.append(pid)
    return sorted(out)


def filter_lines(lines: Sequence[TextLine], page_ids: Iterable[str]) -> list[TextLine]:
    s = set(page_ids)
    return [x for x in lines if x.page in s]


def frequencies(lines: Sequence[TextLine]) -> Counter[str]:
    c: Counter[str] = Counter()
    for line in lines:
        c.update(line.tokens)
    return c


def entropy(counts: dict | Counter) -> float:
    n = sum(counts.values())
    if not n:
        return float("nan")
    h = 0.0
    for c in counts.values():
        if c:
            p = c / n
            h -= p * math.log2(p)
    return h


def mutual_information_pairs(pairs: Sequence[tuple[str, str]]) -> float:
    joint = Counter(pairs)
    left = Counter(a for a, _ in pairs)
    right = Counter(b for _, b in pairs)
    n = len(pairs)
    if not n:
        return 0.0
    out = 0.0
    for (a, b), c in joint.items():
        p = c / n
        out += p * math.log2(p / ((left[a] / n) * (right[b] / n)))
    return out


def first_eva_unit(word: str) -> str:
    g = eva_glyphs(word)
    return g[0] if g else ""


def terminal_records(lines: Sequence[TextLine], across_line: bool = False):
    """Records (stem, terminal, next-initial) for n/l/r terminals.

    If across_line=True, use only physical line-final n/l/r tokens and the next
    physical line's first token on the same page.
    """
    out = []
    if not across_line:
        for line in lines:
            for i in range(len(line.tokens) - 1):
                w = line.tokens[i]
                e = w[-1:] if w else ""
                if e in TERMINALS and len(w) > 1:
                    out.append((w[:-1], e, first_eva_unit(line.tokens[i + 1])))
        return out

    for i, line in enumerate(lines[:-1]):
        if not line.tokens:
            continue
        nxt = lines[i + 1]
        if nxt.page != line.page or not nxt.tokens:
            continue
        w = line.tokens[-1]
        e = w[-1:] if w else ""
        if e in TERMINALS and len(w) > 1:
            out.append((w[:-1], e, first_eva_unit(nxt.tokens[0])))
    return out


def stem_preserving_terminal_permutation_test(
    records: Sequence[tuple[str, str, str]],
    *,
    reps: int = 300,
    seed: int = 246813579,
) -> dict[str, float]:
    """Shuffle next-initials only within each stem, preserving terminal preferences."""
    obs = mutual_information_pairs([(e, nxt) for _, e, nxt in records])
    groups: dict[str, list[int]] = defaultdict(list)
    for i, (stem, _, _) in enumerate(records):
        groups[stem].append(i)
    rng = random.Random(seed)
    nulls = []
    for _ in range(reps):
        work = [list(x) for x in records]
        for idxs in groups.values():
            vals = [work[i][2] for i in idxs]
            rng.shuffle(vals)
            for i, v in zip(idxs, vals):
                work[i][2] = v
        nulls.append(mutual_information_pairs([(e, nxt) for _, e, nxt in work]))
    nulls.sort()
    mean = sum(nulls) / len(nulls)
    p = (1 + sum(x >= obs for x in nulls)) / (len(nulls) + 1)
    return {
        "n": len(records),
        "observed_mi": obs,
        "null_mean": mean,
        "excess_mi": obs - mean,
        "p": p,
        "null_95": nulls[int(0.95 * len(nulls))],
    }


def line_position_stats(lines: Sequence[TextLine]) -> dict[str, dict[str, int | float]]:
    stat: dict[str, Counter[str]] = defaultdict(Counter)
    for line in lines:
        for i, w in enumerate(line.tokens):
            stat[w]["n"] += 1
            stat[w]["last" if i == len(line.tokens) - 1 else "internal"] += 1
    return {
        w: {
            "n": c["n"],
            "internal": c["internal"],
            "last": c["last"],
            "last_rate": c["last"] / c["n"],
        }
        for w, c in stat.items()
    }


def build_segmenter_frequency(lines: Sequence[TextLine]) -> Counter[str]:
    return frequencies(lines)


def candidate_splits(
    word: str,
    freq: Counter[str],
    *,
    min_piece_freq: int = 2,
    alpha: float = 0.1,
    boundary_bonus: float = 1.0,
    corpus_n: int | None = None,
) -> list[dict]:
    """One-boundary split candidates, scored using a unigram likelihood ratio."""
    if corpus_n is None:
        corpus_n = sum(freq.values())
    vocab = len(freq) + 1
    den = corpus_n + alpha * vocab

    def lp(x: str) -> float:
        return math.log((freq.get(x, 0) + alpha) / den)

    g = eva_glyphs(word)
    out = []
    unsplit = lp(word)
    for k in range(2, len(g) - 1):
        a = "".join(g[:k])
        b = "".join(g[k:])
        fa, fb = freq.get(a, 0), freq.get(b, 0)
        if fa < min_piece_freq or fb < min_piece_freq:
            continue
        terminal = g[k - 1] in BOUNDARY_TERMINALS
        score = lp(a) + lp(b) + (boundary_bonus if terminal else 0.0)
        out.append(
            {
                "k": k,
                "a": a,
                "b": b,
                "fa": fa,
                "fb": fb,
                "terminal_boundary": terminal,
                "score": score,
                "llr": score - unsplit,
            }
        )
    return sorted(out, key=lambda x: x["score"], reverse=True)


def viterbi_segment(
    word: str,
    freq: Counter[str],
    *,
    llr_threshold: float = -2.1654,
    boundary_bonus: float = 1.0,
    alpha: float = 0.1,
    min_piece_freq: int = 2,
) -> dict:
    """Multi-piece DP segmenter using the handoff likelihood-ratio convention.

    This reproduces the exploratory style of segmenter; it is *not* a final
    generative model. Each added boundary receives -llr_threshold and an
    optional terminal bonus.
    """
    g = eva_glyphs(word)
    n = sum(freq.values())
    vocab = len(freq) + 1
    den = n + alpha * vocab

    def lp(x: str) -> float:
        return math.log((freq.get(x, 0) + alpha) / den)

    dp: list[dict | None] = [None] * (len(g) + 1)
    dp[0] = {"score": 0.0, "parts": []}
    for j in range(1, len(g) + 1):
        for i in range(j):
            if j - i < 2 or dp[i] is None:
                continue
            seg = "".join(g[i:j])
            if (i > 0 or j < len(g)) and freq.get(seg, 0) < min_piece_freq:
                continue
            score = dp[i]["score"] + lp(seg)
            if i > 0:
                prev = dp[i]["parts"][-1]
                term = eva_glyphs(prev)[-1] in BOUNDARY_TERMINALS
                score += (boundary_bonus if term else 0.0) - llr_threshold
            cand = {"score": score, "parts": dp[i]["parts"] + [seg]}
            if dp[j] is None or score > dp[j]["score"]:
                dp[j] = cand
    unsplit = lp(word)
    best = dp[-1]
    if best is None or best["score"] <= unsplit:
        return {"parts": [word], "score": unsplit, "unsplit": unsplit, "margin": 0.0}
    return {
        "parts": best["parts"],
        "score": best["score"],
        "unsplit": unsplit,
        "margin": best["score"] - unsplit,
    }


def conservative_normalizer(segmented_tokens: Sequence[str]) -> callable:
    """Return a token normalizer used for exploratory family discovery.

    WARNING: this intentionally removes information and must not be treated as
    the final decipherment state. It is useful for identifying paradigms only.
    """
    f = Counter(segmented_tokens)
    terminal_stems = {w[:-1] for w in f if len(w) > 1 and w[-1] in TERMINALS}

    def normalize(w: str) -> str:
        x = w
        if x.endswith("g") and len(x) > 1 and f[x[:-1]] >= 2:
            x = x[:-1]
        if x.startswith("q") and len(x) > 1 and f[x[1:]] >= 2:
            x = x[1:]
        if len(x) > 1 and x[-1] in TERMINALS:
            x = x[:-1]
        elif x.endswith("m") and len(x) > 1 and x[:-1] in terminal_stems:
            x = x[:-1]
        return x

    return normalize


def context_vectors(tokens: Sequence[str], top_context: int = 150) -> dict[str, Counter[str]]:
    f = Counter(tokens)
    top = {w for w, _ in f.most_common(top_context)}
    ctx: dict[str, Counter[str]] = defaultdict(Counter)
    for i, w in enumerate(tokens):
        l = tokens[i - 1] if i else "^"
        r = tokens[i + 1] if i + 1 < len(tokens) else "$"
        ctx[w]["L:" + (l if l in top else "*")] += 1
        ctx[w]["R:" + (r if r in top else "*")] += 1
    return ctx


def cosine_counts(a: Counter[str], b: Counter[str]) -> float:
    aa = sum(v * v for v in a.values())
    bb = sum(v * v for v in b.values())
    if not aa or not bb:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    return dot / math.sqrt(aa * bb)


def prefix_remainder_lattices(
    tokens: Sequence[str],
    *,
    min_form_freq: int = 5,
    prefix_units: int = 2,
    min_shared_remainders: int = 5,
    eva: bool = True,
):
    f = Counter(tokens)
    by_rem: dict[str, dict[str, str]] = defaultdict(dict)
    for w, n in f.items():
        if n < min_form_freq:
            continue
        u = eva_glyphs(w) if eva else list(w)
        if len(u) <= prefix_units:
            continue
        p = "".join(u[:prefix_units])
        r = "".join(u[prefix_units:])
        by_rem[r][p] = w
    pairs: Counter[tuple[str, str]] = Counter()
    examples: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
    for rem, forms in by_rem.items():
        ps = sorted(forms)
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                pair = (ps[i], ps[j])
                pairs[pair] += 1
                examples[pair].append((rem, forms[ps[i]], forms[ps[j]]))
    return [
        {"pair": pair, "shared_remainders": n, "examples": examples[pair]}
        for pair, n in pairs.most_common()
        if n >= min_shared_remainders
    ]


def permutation_corrected_adjacent_mi(tokens: Sequence[str], reps: int = 20, seed: int = 12345) -> float:
    pairs = list(zip(tokens[:-1], tokens[1:]))
    obs = mutual_information_pairs(pairs)
    rng = random.Random(seed)
    null = 0.0
    for _ in range(reps):
        z = list(tokens)
        rng.shuffle(z)
        null += mutual_information_pairs(list(zip(z[:-1], z[1:])))
    return obs - null / reps
