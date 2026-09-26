"""Glen Claston's v101 transcription: parser, ZL3b metadata and v101 -> EVA mapping.

The v101 file (``data/mechanisms/voyn_101.txt``) is latin-1 encoded. Each record
is ``<page.line>body`` with a CRLF ending. In the body ``.`` is a word space,
``,`` an uncertain space, ``-`` ends a line and ``=`` ends a paragraph (labels
and ring texts also end in ``=``). Every other character is treated as one
v101 glyph symbol, except ``*`` and ``?``, which mark unreadable or uncertain
glyphs and make their word unclean (as ``?``/``*`` do in the ZL3b parser).

Lines whose sub-locus is a plain integer (``1r.12``) are "text" lines; all
others (``67r1.outer_ring``, ``68v1.radial.3``, ``rose.nwest_label_1``) are
"label" lines. Currier language, hand and section are borrowed from the ZL3b
page header of the same folio (inline ZL changes, i.e. the f115r hand change,
are applied through the line alignment when a v101 line is aligned to a ZL
line).

The v101 -> EVA mapping is inferred, not assumed: word pairs from aligned lines
are fed to a monotone many-to-one EM aligner in which each v101 symbol emits an
EVA substring of 0..MAX_EMIT characters. See ``infer_mapping``.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V101_PATH = ROOT / "data/mechanisms/voyn_101.txt"
ZL_PATH = ROOT / "data/ZL3b-n.txt"
IT_PATH = ROOT / "data/mechanisms/IT2a-n.txt"

UNCERTAIN = set("*?")
MAX_EMIT = 4
LENGTH_PRIOR = {0: 0.05, 1: 1.0, 2: 0.4, 3: 0.2, 4: 0.05}


# ---------------------------------------------------------------------------
# v101 parsing
# ---------------------------------------------------------------------------

def zl_page(v101_page: str) -> str:
    """Map a v101 page id to the ZL3b page id."""
    if v101_page == "rose":
        return "fRos"
    m = re.fullmatch(r"(\d+[rv])\d?-[rv]\d", v101_page)  # 101r1-r2, 101v2-v1
    if m:
        return "f" + m[1]
    return "f" + v101_page


def folio_of(page: str) -> str:
    m = re.match(r"f\d+", page)
    return m[0] if m else page


def parse_body(body: str):
    """Words and gap kinds for one v101 line body."""
    body = body.rstrip("\r\n")
    end = body[-1:] if body[-1:] in "-=" else ""
    if end:
        body = body[:-1]
    parts = re.split(r"([.,])", body)
    words = []
    for p in parts[::2]:
        clean = bool(p) and not (set(p) & UNCERTAIN)
        words.append({"word": p, "clean": clean})
    gaps = [{".": "ordinary", ",": "uncertain"}[p] for p in parts[1::2]]
    return words, gaps, end


def load_v101(path: Path = V101_PATH) -> list[dict]:
    lines = []
    for raw in path.read_text(encoding="latin-1").splitlines():
        m = re.match(r"^<([^.>]+)\.([^>]+)>(.*)$", raw.rstrip("\r"))
        if not m:
            raise ValueError(f"unparsed v101 record: {raw!r}")
        vpage, sub, body = m.groups()
        words, gaps, end = parse_body(body)
        number = int(sub) if sub.isdigit() else None
        page = zl_page(vpage)
        lines.append(dict(v101_page=vpage, page=page, folio=folio_of(page), sub=sub, number=number,
                          kind="text" if number is not None else "label",
                          locus=f"{page}.{sub}", words=words, gaps=gaps, end=end))
    # Paragraph structure among text lines of a page.
    prev = {}
    for ln in lines:
        if ln["kind"] != "text":
            ln["paragraph_start"] = ln["paragraph_end"] = False
            continue
        p = prev.get(ln["page"])
        ln["paragraph_start"] = p is None or p["end"] == "="
        ln["paragraph_end"] = ln["end"] == "="
        prev[ln["page"]] = ln
    return lines


# ---------------------------------------------------------------------------
# ZL3b (all line types) for alignment and metadata
# ---------------------------------------------------------------------------

def zl_token(raw: str) -> dict:
    uncertain = bool(re.search(r"[?*\[\]{}'’@]", raw))
    clean = re.sub(r"\[([^:\]]*):[^\]]*\]", r"\1", raw)
    clean = clean.replace("{", "").replace("}", "").replace("'", "").replace("’", "")
    return {"word": clean, "clean": not uncertain and bool(re.fullmatch("[a-z]+", clean))}


def load_ivtff_all(path: Path) -> tuple[dict, list[dict]]:
    """Page metadata and every locus line (paragraph, label, circular, radial)."""
    meta, lines = {}, []
    current = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        hm = re.match(r"^<(f[^.> ]+)>\s*<!([^>]*)>", raw)
        if hm:
            meta[hm[1]] = dict(re.findall(r"\$(\w)=([^\s>]+)", hm[2]))
            current[hm[1]] = dict(meta[hm[1]])
            continue
        lm = re.match(r"^<(f[^.>]+)\.(\d+),([^>]*)>\s*(.*)$", raw)
        if not lm:
            continue
        page, body = lm[1], lm[4]
        cur = current.setdefault(page, dict(meta.get(page, {})))
        for change in re.findall(r"<@([^>]*)>", body):
            cur.update(re.findall(r"(\w)=([^\s>]+)", change))
        body = re.sub(r"<!.*?>", "", body)
        body = re.sub(r"<@[^>]*>", "", body)
        body = body.replace("<%>", "").replace("<$>", "").replace("<~>", "")
        parts = re.split(r"<->|[.,]", body.strip().rstrip("-= "))
        lines.append(dict(page=page, number=int(lm[2]), locus=f"{page}.{lm[2]}", descriptor=lm[3],
                          words=[zl_token(p.strip()) for p in parts], meta=dict(cur)))
    return meta, lines


# ---------------------------------------------------------------------------
# EM aligner: each v101 symbol emits an EVA substring of length 0..MAX_EMIT
# ---------------------------------------------------------------------------

@dataclass
class Mapping:
    table: dict[str, dict[str, float]] = field(default_factory=dict)

    def prob(self, c: str, s: str) -> float:
        row = self.table.get(c)
        if row is None:
            return LENGTH_PRIOR.get(len(s), 0.0) * 1e-3
        return row.get(s, 1e-9)

    def best(self, c: str) -> str:
        row = self.table.get(c)
        return max(row.items(), key=lambda kv: kv[1])[0] if row else "?"


def _forward(v: str, e: str, mp: Mapping):
    n, m = len(v), len(e)
    a = [[0.0] * (m + 1) for _ in range(n + 1)]
    a[0][0] = 1.0
    for i in range(1, n + 1):
        c = v[i - 1]
        ai, ap = a[i], a[i - 1]
        for j in range(0, m + 1):
            tot = 0.0
            for k in range(0, min(MAX_EMIT, j) + 1):
                if ap[j - k]:
                    tot += ap[j - k] * mp.prob(c, e[j - k:j])
            ai[j] = tot
    return a


def _backward(v: str, e: str, mp: Mapping):
    n, m = len(v), len(e)
    b = [[0.0] * (m + 1) for _ in range(n + 1)]
    b[n][m] = 1.0
    for i in range(n - 1, -1, -1):
        c = v[i]
        bi, bn = b[i], b[i + 1]
        for j in range(m, -1, -1):
            tot = 0.0
            for k in range(0, min(MAX_EMIT, m - j) + 1):
                if bn[j + k]:
                    tot += mp.prob(c, e[j:j + k]) * bn[j + k]
            bi[j] = tot
    return b


def em_step(pairs, mp: Mapping) -> tuple[Mapping, float]:
    counts: dict[str, Counter] = defaultdict(Counter)
    loglik = 0.0
    for v, e in pairs:
        a = _forward(v, e, mp)
        Z = a[len(v)][len(e)]
        if Z <= 0:
            continue
        loglik += math.log(Z)
        b = _backward(v, e, mp)
        for i in range(1, len(v) + 1):
            c = v[i - 1]
            for j in range(len(e) + 1):
                if not b[i][j]:
                    continue
                for k in range(0, min(MAX_EMIT, j) + 1):
                    if a[i - 1][j - k]:
                        w = a[i - 1][j - k] * mp.prob(c, e[j - k:j]) * b[i][j] / Z
                        if w > 1e-12:
                            counts[c][e[j - k:j]] += w
    table = {}
    for c, cnt in counts.items():
        tot = sum(cnt.values())
        table[c] = {s: x / tot for s, x in cnt.items() if x / tot > 1e-6}
    return Mapping(table), loglik


def initial_mapping(pairs) -> Mapping:
    """Uniform over substrings seen with each symbol, weighted by a length prior."""
    seen: dict[str, Counter] = defaultdict(Counter)
    for v, e in pairs:
        subs = {e[j:j + k] for j in range(len(e) + 1) for k in range(0, MAX_EMIT + 1) if j + k <= len(e)}
        for c in set(v):
            for s in subs:
                seen[c][s] += LENGTH_PRIOR[len(s)]
    table = {}
    for c, cnt in seen.items():
        tot = sum(cnt.values())
        table[c] = {s: x / tot for s, x in cnt.items()}
    return Mapping(table)


def viterbi(v: str, e: str, mp: Mapping) -> list[str] | None:
    n, m = len(v), len(e)
    NEG = -1e18
    d = [[NEG] * (m + 1) for _ in range(n + 1)]
    bp = [[0] * (m + 1) for _ in range(n + 1)]
    d[0][0] = 0.0
    for i in range(1, n + 1):
        c = v[i - 1]
        for j in range(m + 1):
            for k in range(0, min(MAX_EMIT, j) + 1):
                if d[i - 1][j - k] <= NEG:
                    continue
                p = mp.prob(c, e[j - k:j])
                if p <= 0:
                    continue
                s = d[i - 1][j - k] + math.log(p)
                if s > d[i][j]:
                    d[i][j], bp[i][j] = s, k
    if d[n][m] <= NEG:
        return None
    out, j = [], m
    for i in range(n, 0, -1):
        k = bp[i][j]
        out.append(e[j - k:j])
        j -= k
    return out[::-1]


def transliterate(word: str, mp: Mapping) -> str:
    return "".join(mp.best(c) for c in word)


# ---------------------------------------------------------------------------
# Alignment of v101 lines/words to ZL lines/words
# ---------------------------------------------------------------------------

def edit_distance(a, b) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def norm_dist(a: str, b: str) -> float:
    return edit_distance(a, b) / max(len(a), len(b), 1)


def align_sequences(a: list, b: list, cost, gap: float):
    """Global alignment; returns list of (i, j) matched index pairs."""
    n, m = len(a), len(b)
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    B = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0], B[i][0] = i * gap, 1
    for j in range(1, m + 1):
        D[0][j], B[0][j] = j * gap, 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            opts = (D[i - 1][j - 1] + cost(a[i - 1], b[j - 1]), D[i - 1][j] + gap, D[i][j - 1] + gap)
            k = min(range(3), key=lambda t: opts[t])
            D[i][j], B[i][j] = opts[k], k
    out, i, j = [], n, m
    while i > 0 or j > 0:
        k = B[i][j] if i > 0 and j > 0 else (1 if i > 0 else 2)
        if k == 0:
            out.append((i - 1, j - 1)); i -= 1; j -= 1
        elif k == 1:
            i -= 1
        else:
            j -= 1
    return out[::-1]


def line_string(words, f=lambda w: w) -> str:
    return ".".join(f(w["word"]) for w in words)


def align_pages(vlines: list[dict], zlines: list[dict], mp: Mapping, max_line_dist: float = 0.6):
    """Match v101 text lines to ZL lines page by page; returns (v101 line, ZL line) pairs."""
    zby = defaultdict(list)
    for z in zlines:
        zby[z["page"]].append(z)
    vby = defaultdict(list)
    for v in vlines:
        if v["kind"] == "text":
            vby[v["page"]].append(v)
    out = []
    for page, vs in vby.items():
        zs = zby.get(page, [])
        if not zs:
            continue
        vstr = [line_string(v["words"], lambda w: transliterate(w, mp)) for v in vs]
        zstr = [line_string(z["words"]) for z in zs]
        cost = lambda i, j: norm_dist(vstr[i], zstr[j])
        pairs = align_sequences(list(range(len(vs))), list(range(len(zs))), cost, gap=0.75)
        out.extend((vs[i], zs[j]) for i, j in pairs if cost(i, j) <= max_line_dist)
    return out


def align_words(vline: dict, zline: dict, mp: Mapping):
    """Word-level alignment inside a matched line pair; returns (v word dict, z word dict, dist)."""
    vw, zw = vline["words"], zline["words"]
    tv = [transliterate(w["word"], mp) for w in vw]
    cost = lambda i, j: norm_dist(tv[i], zw[j]["word"])
    pairs = align_sequences(list(range(len(vw))), list(range(len(zw))), cost, gap=0.6)
    return [(vw[i], zw[j], cost(i, j), i, j) for i, j in pairs]


def seed_pairs(vlines, zlines):
    """Initial word pairs: same page/line number, same word count, all clean."""
    zmap = {(z["page"], z["number"]): z for z in zlines}
    out = []
    for v in vlines:
        if v["kind"] != "text":
            continue
        z = zmap.get((v["page"], v["number"]))
        if z is None or len(z["words"]) != len(v["words"]):
            continue
        for a, b in zip(v["words"], z["words"]):
            if a["clean"] and b["clean"] and 0.4 <= len(a["word"]) / len(b["word"]) <= 1.6:
                out.append((a["word"], b["word"]))
    return out


def infer_mapping(vlines, zlines, *, rounds: int = 3, em_iters: int = 8, accept: float = 0.5, log=print):
    """Bootstrap: seed pairs -> EM -> realign lines and words -> EM on accepted pairs."""
    pairs = seed_pairs(vlines, zlines)
    log(f"seed word pairs: {len(pairs)}")
    mp = initial_mapping(pairs)
    history = []
    for r in range(rounds):
        for it in range(em_iters):
            mp, ll = em_step(pairs, mp)
        history.append(dict(round=r, pairs=len(pairs), loglik=ll))
        log(f"round {r}: {len(pairs)} pairs, loglik {ll:.1f}")
        if r == rounds - 1:
            break
        matched = align_pages(vlines, zlines, mp)
        pairs = []
        for vl, zl in matched:
            for a, b, d, _, _ in align_words(vl, zl, mp):
                if a["clean"] and b["clean"] and d <= accept:
                    pairs.append((a["word"], b["word"]))
    return mp, history


# ---------------------------------------------------------------------------
# Classes: v101 symbols that EVA merges
# ---------------------------------------------------------------------------

def merged_sets(mp: Mapping, symbol_counts: Counter, min_count: int = 1) -> dict[str, list[str]]:
    """EVA image -> v101 symbols (most frequent first) with that argmax image."""
    sets = defaultdict(list)
    for c in mp.table:
        if symbol_counts[c] >= min_count:
            sets[mp.best(c)].append(c)
    return {k: sorted(v, key=lambda c: (-symbol_counts[c], c)) for k, v in sets.items()}


def collapse_table(mp: Mapping, symbol_counts: Counter) -> dict[str, str]:
    """Each v101 symbol -> canonical (most frequent) v101 symbol of its EVA class."""
    sets = merged_sets(mp, symbol_counts)
    return {c: members[0] for members in sets.values() for c in members}


def collapse(word: str, table: dict[str, str]) -> str:
    return "".join(table.get(c, c) for c in word)
