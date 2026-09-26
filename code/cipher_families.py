"""Cipher families, layout modifier and alphabet-independent fingerprints (CIPHER_FAMILY_PROTOCOL.md).

Every generator returns (tokens, labels): the cipher tokens and, for
homophonic families, the plaintext unit each token encodes (None otherwise).
"""
from __future__ import annotations

import importlib.util
import itertools
import math
import random
import re
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

import numpy as np

import mechanism_models as mm
import slot_cipher as sc
from voynich_core import eva_glyphs

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
_spec = importlib.util.spec_from_file_location("frontier", Path(__file__).with_name("06_boundary_frontier.py"))
frontier = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(frontier)

WINDOW = 5000
TOP_TYPES = 200
PERMS = 20
FP_SEED = 20260926
LANGUAGES = {"latin": "latin_alfonsi.txt", "italian": "italian_dante.txt", "german": "mhg_fh.txt"}
LI, LF, PF = "↑", "↓", "¶"   # layout signs, used nowhere else
SUFFIXES = sorted({"orum", "ibus", "tur", "bus", "que", "us", "um", "is", "em", "ur", "er", "re",
                   "one", "are", "ato", "en", "ent"}, key=lambda s: (-len(s), s))
PREFIXES = sorted({"con", "per", "pro", "prae"}, key=lambda s: (-len(s), s))
VOWELS = set("aeiouy")
PRIMARY = ["P1_ttr", "P2_hapax", "P3_top10", "P4_repeat", "P5_adj_mi", "P6_page_mi",
           "P7_line_initial_mi", "P8_line_final_mi", "P9_para_first_mi"]
SECONDARY = ["S_len_units", "S_within_h", "S_edge_mi", "S_first_unit_li_mi", "S_last_unit_lf_mi"]


# ---------------------------------------------------------------------------
# Targets and layout
# ---------------------------------------------------------------------------

def currier_b_windows(path=DATA / "ZL3b-n.txt"):
    """(W1 lines, W2 lines, training lines) from ZL3b Currier B P0 lines in file order."""
    lines = [ln for ln in frontier.load_lines(path) if ln["meta"].get("L") == "B"]
    pages = OrderedDict()
    for ln in lines:
        pages.setdefault(ln["page"], []).append(ln)
    windows, cur, total = [[], []], 0, 0
    for page, ls in pages.items():
        if cur < 2:
            windows[cur].append(page)
            total += sum(len(ln["words"]) for ln in ls)
            if total >= WINDOW:
                cur, total = cur + 1, 0
    w1, w2 = set(windows[0]), set(windows[1])
    pick = lambda s: [ln for ln in lines if ln["page"] in s]
    return pick(w1), pick(w2), [ln for ln in lines if ln["page"] not in w1 | w2]


def slots(lines):
    return sum(len(ln["words"]) for ln in lines)


def apply_layout_rule(lines, rng):
    """L1: line-initial / line-final / paragraph-first-line signs."""
    out = []
    for ln in lines:
        words = [dict(w) for w in ln["words"]]
        if words and words[0]["clean"] and rng.random() < 0.5:
            words[0]["word"] = LI + words[0]["word"]
        if words and words[-1]["clean"] and rng.random() < 0.5:
            words[-1]["word"] = words[-1]["word"] + LF
        if ln["paragraph_start"]:
            for w in words:
                if w["clean"] and rng.random() < 0.3:
                    w["word"] = PF + w["word"]
        out.append(dict(ln, words=words))
    return out


# ---------------------------------------------------------------------------
# Plaintexts
# ---------------------------------------------------------------------------

_PLAIN = {}


def plain_words(language):
    if language not in _PLAIN:
        _PLAIN[language] = sc.latin_words((DATA / LANGUAGES[language]).read_text(encoding="utf-8", errors="replace"))
    return _PLAIN[language]


def passage(seq, need, rng):
    if len(seq) < need:
        return None
    start = rng.randrange(len(seq) - need + 1)
    return seq[start:start + need]


# ---------------------------------------------------------------------------
# Families
# ---------------------------------------------------------------------------

def sym(i, base=0xE000):
    return chr(base + i)


def homophone_table(words, k):
    freq = Counter(c for w in words for c in w)
    letters = sorted(freq, key=lambda c: (-freq[c], c))
    L = len(letters); total = sum(freq.values())
    alloc = {c: 1 + round((k - L) * freq[c] / total) for c in letters}
    diff = k - sum(alloc.values())
    i = 0
    while diff != 0:
        c = letters[i % L]
        if diff > 0:
            alloc[c] += 1; diff -= 1
        elif alloc[c] > 1:
            alloc[c] -= 1; diff += 1
        i += 1
    table, n = {}, 0
    for c in letters:
        table[c] = [sym(n + j) for j in range(alloc[c])]
        n += alloc[c]
    return table


def gen_plain(n, rng, language, **_):
    ws = passage(plain_words(language), n, rng)
    return (None, None) if ws is None else (list(ws), list(ws))


def gen_homophonic(n, rng, language, k, **_):
    ws = passage(plain_words(language), n, rng)
    if ws is None:
        return None, None
    table = homophone_table(plain_words(language), k)
    return ["".join(rng.choice(table[c]) for c in w) for w in ws], list(ws)


def code_strings(count, rng):
    alphabet = [sym(i, 0xE400) for i in range(8)]
    pool = ["".join(p) for L in (2, 3, 4) for p in itertools.product(alphabet, repeat=L)]
    rng.shuffle(pool)
    return pool[:count]


def gen_nomenclator(n, rng, language, N, v, **_):
    ws = passage(plain_words(language), n, rng)
    if ws is None:
        return None, None
    allw = plain_words(language)
    top = [w for w, _ in Counter(allw).most_common(N)]
    codes = code_strings(N * v, rng)
    book = {w: codes[i * v:(i + 1) * v] for i, w in enumerate(top)}
    table = homophone_table(allw, 40)
    toks = [rng.choice(book[w]) if w in book else "".join(rng.choice(table[c]) for c in w) for w in ws]
    return toks, list(ws)


def abbreviate(w, p, rng):
    pre = next((x for x in PREFIXES if w.startswith(x) and len(w) > len(x) + 1), None)
    head = ("<" + pre + ">") if pre else ""
    body = w[len(pre):] if pre else w
    suf = next((x for x in SUFFIXES if body.endswith(x) and len(body) > len(x)), None)
    tail = ("[" + suf + "]") if suf else ""
    core = body[:-len(suf)] if suf else body
    if len(w) >= 4 and len(core) > 2:
        core = core[0] + "".join(c for c in core[1:-1] if c not in VOWELS or rng.random() >= p) + core[-1]
    return head + core + tail


def gen_abbreviation(n, rng, language, p, **_):
    ws = passage(plain_words(language), n, rng)
    if ws is None:
        return None, None
    return [abbreviate(w, p, rng) for w in ws], list(ws)


_ENCODER = None


def encoder():
    global _ENCODER
    if _ENCODER is None:
        _ENCODER = mm.Encoder(DATA / "mechanisms/naibbe_tables.csv")
    return _ENCODER


def gen_naibbe(n, rng, language, level, coupling, training, **_):
    letters = mm.clean_plain(" ".join(plain_words(language)))
    need = 3 * n + 10
    if len(letters) < need:
        return None, None
    start = rng.randrange(len(letters) - need + 1)
    text = letters[start:start + need]
    # mm.generate starts inside the first third; 3 letters/token leaves at least 2 per token after it.
    words, audit = mm.generate(training, encoder(), text, n, dict(mechanism="encoding", level=level, coupling=coupling),
                               rng.randrange(10 ** 9))
    if audit["source_wraps"]:
        return None, None
    return words, [encoder().reverse[w] for w in words]


def gen_syllabic(n, rng, language, h, s, beta, training, **_):
    syll = [x for w in plain_words(language) for x in sc.syllabify(w)]
    part = passage(syll, n, rng)
    if part is None:
        return None, None
    config = sc.Config(h, float(s), float(beta))
    seed = rng.randrange(10 ** 9)
    book = sc.CodeBook(set(part), training, config, seed)
    words = sc.encipher(part, book, training.edge, config, seed + 5000)
    return words, list(part)


def gen_nulls(n, rng, language, r, nulls, training, **_):
    base, labels = gen_naibbe(n, rng, language, 1, 0, training)
    if base is None:
        return None, None
    fixed = [training.fresh(rng) for _ in range(20)]
    toks, labs, i = [], [], 0
    while len(toks) < n:
        if rng.random() < r:
            w = training.fresh(rng) if nulls == "fresh" else rng.choice(fixed)
            toks.append(w); labs.append("NULL:" + w)
        else:
            toks.append(base[i]); labs.append(labels[i]); i += 1
    return toks, labs


def gen_reference(n, rng, mechanism, level, coupling, training, **_):
    words, _ = mm.generate(training, None, "x" * 30, n, dict(mechanism=mechanism, level=level, coupling=coupling),
                           rng.randrange(10 ** 9))
    return words, None


FAMILIES = {
    "F1_plain": (gen_plain, [{}], True),
    "F2_homophonic": (gen_homophonic, [dict(k=k) for k in (40, 60, 90)], True),
    "F3_nomenclator": (gen_nomenclator, [dict(N=N, v=v) for N in (30, 100, 300) for v in (1, 3)], True),
    "F4_abbreviation": (gen_abbreviation, [dict(p=p) for p in (0.3, 0.7)], True),
    "F5_verbose_naibbe": (gen_naibbe, [dict(level=l, coupling=c) for l in (0, 1, 2) for c in (0, 1)], True),
    "F6_verbose_syllabic": (gen_syllabic, [dict(h=h, s=s, beta=b) for h in (2, 4, 8) for s in (0, 1) for b in (0, 2)], True),
    "F7_verbose_nulls": (gen_nulls, [dict(r=r, nulls=x) for r in (0.10, 0.25) for x in ("fresh", "fixed")], True),
    "R1_assembly": (gen_reference, [dict(mechanism="assembly", level=l, coupling=c) for l in (0, 1, 2) for c in (0, 1)], False),
    "R2_copy": (gen_reference, [dict(mechanism="copy", level=l, coupling=c) for l in (0, 1, 2) for c in (0, 1)], False),
}
EVA_UNIT_FAMILIES = {"F5_verbose_naibbe", "F6_verbose_syllabic", "F7_verbose_nulls", "R1_assembly", "R2_copy"}


def configurations():
    for fam, (_, grid, uses_language) in FAMILIES.items():
        for params in grid:
            for language in (LANGUAGES if uses_language else [None]):
                for layout in ("L0", "L1"):
                    yield dict(family=fam, params=params, language=language, layout=layout)


def config_key(c):
    p = ",".join(f"{k}={v}" for k, v in sorted(c["params"].items()))
    return f"{c['family']}|{p}|{c['language']}|{c['layout']}"


def simulate(config, window, seed, training):
    """Laid-out lines for one configuration and seed, or None if the plaintext cannot fill the window."""
    gen = FAMILIES[config["family"]][0]
    rng = random.Random(seed)
    n = slots(window)
    kwargs = dict(config["params"], training=training)
    if config["language"]:
        kwargs["language"] = config["language"]
    toks, labels = gen(n, rng, **kwargs)
    if toks is None:
        return None, None
    assert len(toks) == n
    laid = mm.apply_template(window, toks)
    if config["layout"] == "L1":
        laid = apply_layout_rule(laid, random.Random(seed + 777))
    return laid, labels


# ---------------------------------------------------------------------------
# Fingerprints
# ---------------------------------------------------------------------------

def mi_codes(a, b):
    a = np.asarray(a); b = np.asarray(b)
    if len(a) == 0:
        return 0.0
    na, nb = a.max() + 1, b.max() + 1
    joint = np.bincount(a * nb + b, minlength=na * nb).reshape(na, nb) / len(a)
    pa = joint.sum(1, keepdims=True); pb = joint.sum(0, keepdims=True)
    nz = joint > 0
    return float((joint[nz] * np.log2(joint[nz] / (pa @ pb)[nz])).sum())


def encode(values):
    idx = {}
    return np.array([idx.setdefault(v, len(idx)) for v in values])


def corrected(a, b, groups, rng, permute="b"):
    """MI minus mean MI after permuting one side within groups (None = globally)."""
    obs = mi_codes(a, b)
    a = np.asarray(a); b = np.asarray(b)
    target = b if permute == "b" else a
    if groups is None:
        blocks = [np.arange(len(target))]
    else:
        g = np.asarray(groups); blocks = [np.where(g == x)[0] for x in np.unique(g)]
    null = []
    for _ in range(PERMS):
        t = target.copy()
        for blk in blocks:
            t[blk] = t[rng.permutation(blk)]
        null.append(mi_codes(a, t) if permute == "b" else mi_codes(t, b))
    return obs - float(np.mean(null))


def fingerprint(lines, units="eva"):
    rng = np.random.default_rng(FP_SEED)
    unit = (lambda w: eva_glyphs(w)) if units == "eva" else list
    clean = [w["word"] for ln in lines for w in ln["words"] if w["clean"]]
    counts = Counter(clean)
    top = {w for w, _ in counts.most_common(TOP_TYPES)}
    cap = lambda w: w if w in top else "*"
    d = {"tokens": len(clean), "types": len(counts)}
    d["P1_ttr"] = len(counts) / len(clean)
    d["P2_hapax"] = sum(v == 1 for v in counts.values()) / len(counts)
    d["P3_top10"] = sum(v for _, v in counts.most_common(10)) / len(clean)
    # P4: adjacent repeats within page (lines may be crossed; unclean slots break).
    pages = defaultdict(list)
    for ln in lines:
        pages[ln["page"]].extend(w["word"] if w["clean"] else None for w in ln["words"])
    rep = exp = npairs = 0
    for seq in pages.values():
        cl = [w for w in seq if w is not None]; c = Counter(cl); nn = len(cl)
        coll = sum(v * (v - 1) for v in c.values()) / max(1, nn * (nn - 1))
        pairs = [(a, b) for a, b in zip(seq, seq[1:]) if a is not None and b is not None]
        rep += sum(a == b for a, b in pairs); exp += coll * len(pairs); npairs += len(pairs)
    d["P4_repeat"] = (rep - exp) / max(1, npairs)
    # Token table with positions.
    rows = []
    for ln in lines:
        ws = ln["words"]
        for i, w in enumerate(ws):
            if w["clean"]:
                rows.append((cap(w["word"]), ln["page"], i == 0, i == len(ws) - 1, bool(ln["paragraph_start"])))
    T = encode([r[0] for r in rows]); P = encode([r[1] for r in rows])
    d["P6_page_mi"] = corrected(T, P, None, rng)
    for key, k in (("P7_line_initial_mi", 2), ("P8_line_final_mi", 3), ("P9_para_first_mi", 4)):
        d[key] = corrected(np.array([int(r[k]) for r in rows]), T, P, rng)
    adj = [(cap(a["word"]), cap(b["word"]), ln["page"]) for ln in lines
           for a, b in zip(ln["words"], ln["words"][1:]) if a["clean"] and b["clean"]]
    enc = encode([x for a, b, _ in adj for x in (a, b)])
    d["P5_adj_mi"] = corrected(enc[0::2], enc[1::2], encode([p for *_, p in adj]), rng)
    # Secondary, unit level.
    gl = {w: unit(w) for w in counts}
    d["S_len_units"] = float(np.mean([len(gl[w]) for w in clean]))
    trans = Counter((a, b) for w in clean for a, b in zip(gl[w], gl[w][1:]))
    left = Counter()
    for (a, _), v in trans.items():
        left[a] += v
    tot = sum(trans.values())
    d["S_within_h"] = -sum(v / tot * math.log2(v / left[a]) for (a, _), v in trans.items()) if tot else 0.0
    e = [(gl[a["word"]][-1], gl[b["word"]][0], ln["page"]) for ln in lines
         for a, b in zip(ln["words"], ln["words"][1:]) if a["clean"] and b["clean"]]
    ee = encode([x for a, b, _ in e for x in (a, b)])
    d["S_edge_mi"] = corrected(ee[0::2], ee[1::2], encode([p for *_, p in e]), rng)
    full_first, full_last = [], []
    for ln in lines:
        for w in ln["words"]:
            if w["clean"]:
                full_first.append(gl[w["word"]][0]); full_last.append(gl[w["word"]][-1])
    d["S_first_unit_li_mi"] = corrected(np.array([int(r[2]) for r in rows]), encode(full_first), P, rng)
    d["S_last_unit_lf_mi"] = corrected(np.array([int(r[3]) for r in rows]), encode(full_last), P, rng)
    return d


def page_bootstrap(lines, reps, seed, units="eva"):
    """Fingerprints of page-resampled windows (duplicated pages get distinct page ids)."""
    pages = OrderedDict()
    for ln in lines:
        pages.setdefault(ln["page"], []).append(ln)
    keys = list(pages)
    rng = random.Random(seed)
    out = []
    for r in range(reps):
        pick = [rng.choice(keys) for _ in keys]
        boot = [dict(ln, page=f"{p}#{j}") for j, p in enumerate(pick) for ln in pages[p]]
        out.append(fingerprint(boot, units))
    return out
