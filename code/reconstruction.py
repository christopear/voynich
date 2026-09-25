"""Reconstructions of handoff claims whose original drivers were lost.

Each ``claim_*`` function recomputes one group of numbers recorded in
``results/results_snapshot.json`` / ``CONTINUATION.md`` from local data, using
an explicit definition. The definitions were recovered by testing plausible
readings of the handoff text against the recorded values; where several
readings were tried, the alternatives and their results are returned too so the
search is visible rather than silently tuned. See
``RECONSTRUCTION_FINDINGS_2026-09-25.md`` for interpretation.

Status vocabulary used in every result:

* ``exact`` - matches the recorded value at its reported precision.
* ``within_noise`` - differs only by Monte Carlo (shuffle/seed) variation.
* ``approximate`` - same regime; original definition not fully recoverable.
* ``qualitative`` - direction/significance reproduced, magnitudes differ.
* ``not_reproduced`` - recorded value not recovered by any tried definition.
"""
from __future__ import annotations

import math
import random
import re
import statistics
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Sequence

from voynich_core import (
    BOUNDARY_TERMINALS,
    TextLine,
    candidate_splits,
    conservative_normalizer,
    context_vectors,
    cosine_counts,
    eva_glyphs,
    filter_lines,
    first_eva_unit,
    line_position_stats,
    mutual_information_pairs,
    permutation_corrected_adjacent_mi,
    prefix_remainder_lattices,
    select_pages,
    stem_preserving_terminal_permutation_test,
    terminal_records,
    viterbi_segment,
)

LLR_THRESHOLD = -2.1654


def result(claim, snapshot, reconstructed, status, definition, **extra):
    return {
        "claim": claim,
        "snapshot": snapshot,
        "reconstructed": reconstructed,
        "status": status,
        "definition": definition,
        **extra,
    }


# ---------------------------------------------------------------------------
# Shared corpora
# ---------------------------------------------------------------------------

class Corpora:
    """Lazily built token sequences shared by several claims."""

    def __init__(self, data: Path, pages, lines: Sequence[TextLine]):
        self.data = data
        self.pages = pages
        self.lines = list(lines)
        self.full = [w for L in self.lines for w in L.tokens]
        self.freq = Counter(self.full)
        self.herbal_pids = select_pages(pages, section="H", currier="A", hand="1")
        self.herbal = filter_lines(self.lines, self.herbal_pids)
        self.herbal_tokens = [w for L in self.herbal for w in L.tokens]
        self._lopo = None
        self._full_seg = None

    def lopo_segmented_herbal(self) -> list[str]:
        """Herbal-A/Hand-1 tokens segmented with leave-one-page-out frequencies."""
        if self._lopo is None:
            out = []
            for pid in self.herbal_pids:
                freq = Counter(w for L in self.herbal if L.page != pid for w in L.tokens)
                for L in self.herbal:
                    if L.page == pid:
                        for w in L.tokens:
                            out += viterbi_segment(w, freq)["parts"]
            self._lopo = out
        return self._lopo

    def segmented_full(self) -> list[str]:
        """Whole-corpus tokens segmented with whole-corpus frequencies (exploratory)."""
        if self._full_seg is None:
            out = []
            for w in self.full:
                out += viterbi_segment(w, self.freq)["parts"]
            self._full_seg = out
        return self._full_seg

    def text_words(self, name: str) -> list[str]:
        text = (self.data / name).read_text(encoding="utf-8", errors="replace").lower()
        return re.findall(r"[^\W\d_]+", text)

    def split_tokens(self, name: str) -> list[str]:
        return (self.data / name).read_text(encoding="utf-8").split()

    def token_lines(self, name: str) -> list[list[str]]:
        return [x.split() for x in (self.data / name).read_text(encoding="utf-8").splitlines()]


# ---------------------------------------------------------------------------
# Terminal system (CONTINUATION sections 4, 15)
# ---------------------------------------------------------------------------

def claim_m_line_final(c: Corpora) -> dict:
    pos = line_position_stats(c.lines)
    grid = []
    for sibset in ("rl", "nlr"):
        for min_m in (1, 2, 3, 5):
            for min_sib in (1, 5, 10):
                mn = ml = sn = sl = 0
                for w, z in pos.items():
                    if not w.endswith("m") or len(w) < 2 or z["n"] < min_m:
                        continue
                    sibs = [w[:-1] + x for x in sibset
                            if w[:-1] + x in pos and pos[w[:-1] + x]["n"] >= min_sib]
                    if not sibs:
                        continue
                    mn += z["n"]; ml += z["last"]
                    sn += sum(pos[s]["n"] for s in sibs); sl += sum(pos[s]["last"] for s in sibs)
                grid.append({"siblings": sibset, "min_m_freq": min_m, "min_sibling_freq": min_sib,
                             "m_tokens": mn, "m_line_final": ml / mn,
                             "sibling_tokens": sn, "sibling_line_final": sl / sn,
                             "enrichment": (ml / mn) / (sl / sn)})
    primary = grid[0]
    return result(
        "same-stem m forms line-final vs r/l siblings",
        {"m": 0.685, "siblings": 0.079, "enrichment": 8.7},
        {"m": primary["m_line_final"], "siblings": primary["sibling_line_final"],
         "enrichment": primary["enrichment"]},
        "approximate",
        "Full corpus, P lines. Every m-final type with an attested stem+r or stem+l "
        "type; token-level line-final rates pooled over m forms and over siblings.",
        range_over_grid={
            "m": [min(g["m_line_final"] for g in grid), max(g["m_line_final"] for g in grid)],
            "siblings": [min(g["sibling_line_final"] for g in grid), max(g["sibling_line_final"] for g in grid)],
            "enrichment": [min(g["enrichment"] for g in grid), max(g["enrichment"] for g in grid)],
        },
        grid=grid,
    )


def claim_internal_m_sibling(c: Corpora) -> dict:
    tot = sib = 0
    for L in c.lines:
        for w in L.tokens[:-1]:
            if w.endswith("m") and len(w) > 1:
                tot += 1
                sib += any(c.freq[w[:-1] + x] for x in "nlr")
    return result(
        "internal (non-line-final) m tokens with an attested same-stem n/l/r sibling",
        85.4, 100 * sib / tot, "exact",
        "Full corpus; tokens ending m, length >=2, not last on their physical line; "
        "sibling = stem+n/l/r attested anywhere in the corpus.",
        n_internal_m_tokens=tot, with_sibling=sib,
    )


def claim_rl_families(c: Corpora, reps: int = 200, seed: int = 1) -> dict:
    rec: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for L in c.lines:
        for a, b in zip(L.tokens, L.tokens[1:]):
            if len(a) > 1 and a[-1] in "rl":
                rec[a[:-1]].append((a[-1], first_eva_unit(b)))
    fams = [s for s, v in rec.items()
            if sum(t == "r" for t, _ in v) >= 10 and sum(t == "l" for t, _ in v) >= 10]
    rng = random.Random(seed)
    sig = []
    for s in fams:
        v = rec[s]
        obs = mutual_information_pairs(v)
        T = [t for t, _ in v]; I = [i for _, i in v]
        null = []
        for _ in range(reps):
            rng.shuffle(T)
            null.append(mutual_information_pairs(list(zip(T, I))))
        null.sort()
        if obs > null[int(0.95 * reps)]:
            sig.append(s)
    return result(
        "same-stem r/l families whose following-initial distribution differs beyond the 95th percentile",
        {"families": 48, "significant": 16},
        {"families": len(fams), "significant": len(sig)},
        "exact",
        "Full corpus, within-line pairs. Family = stem with >=10 stem+r and >=10 stem+l "
        f"tokens followed by a token on the same line. Statistic MI(terminal; next EVA "
        f"initial); null relabels r/l within the family ({reps} shuffles, seed {seed}).",
        significant_stems=sig,
        note="Uncorrected per-family tests; with 48 tests ~2.4 false positives are expected at 5%.",
    )


def claim_context_cosines(c: Corpora, seed: int = 20260925) -> dict:
    pairs = [("chor", "chol"), ("otchor", "otchol"), ("chom", "cham"), ("shor", "shol")]
    claimed = [0.737, 0.716, 0.658, 0.653]
    tried = {}
    for top in (50, 100, 150, 200, 300):
        ctx = context_vectors(c.full, top_context=top)
        tried[f"voynich_core.context_vectors(top={top})"] = [cosine_counts(ctx[a], ctx[b]) for a, b in pairs]
    for within_line in (False, True):
        for top in (None, 150, 300):
            ctx = _word_contexts(c, within_line, top)
            tried[f"word contexts, no catch-all, top={top}, within_line={within_line}"] = [
                cosine_counts(ctx[a], ctx[b]) for a, b in pairs]
    ctx = defaultdict(Counter)
    for L in c.lines:
        s = L.tokens
        for i, w in enumerate(s):
            if i: ctx[w]["L:" + first_eva_unit(s[i - 1])] += 1
            if i + 1 < len(s): ctx[w]["R:" + first_eva_unit(s[i + 1])] += 1
    tried["neighbour initial glyphs, within line"] = [cosine_counts(ctx[a], ctx[b]) for a, b in pairs]

    # Substitute test of the underlying claim with documented representations:
    # same-stem n/l/r/m pairs vs frequency-matched unrelated pairs.
    stems = defaultdict(list)
    for w, n in c.freq.items():
        if n >= 10 and len(w) > 2 and w[-1] in "nlrm":
            stems[w[:-1]].append(w)
    sib_pairs = [(a, b) for v in stems.values() for i, a in enumerate(sorted(v)) for b in sorted(v)[i + 1:]]
    pool = sorted(w for w, n in c.freq.items() if n >= 10)
    rng = random.Random(seed)
    controls = []
    for a, b in sib_pairs:
        fb = c.freq[b]
        controls.append(rng.choice([w for w in pool if 0.8 * fb <= c.freq[w] <= 1.25 * fb and w[:-1] != a[:-1]]))
    substitute = {}
    for label, ctx in (("context_vectors(top=150), with catch-all", context_vectors(c.full, top_context=150)),
                       ("top-150 word contexts, catch-all dropped", _word_contexts(c, False, 150))):
        same = [cosine_counts(ctx[a], ctx[b]) for a, b in sib_pairs]
        ctrl = [cosine_counts(ctx[a], ctx[z]) for (a, _), z in zip(sib_pairs, controls)]
        substitute[label] = {"same_stem_median": statistics.median(same),
                             "matched_control_median": statistics.median(ctrl),
                             "same_stem_higher_fraction": sum(x > y for x, y in zip(same, ctrl)) / len(same)}
    return result(
        "contextual cosine of same-stem terminal pairs (chor/chol 0.737 etc.)",
        dict(zip(["/".join(p) for p in pairs], claimed)),
        dict(zip(["/".join(p) for p in pairs], tried["voynich_core.context_vectors(top=150)"])),
        "not_reproduced",
        "Recorded cosines could not be recovered; the representation used is unknown. "
        "voynich_core.context_vectors pools rare neighbours into a shared catch-all "
        "dimension, which inflates cosines towards 1.",
        representations_tried=tried,
        substitute_test={
            "definition": "Full corpus. All same-stem pairs among n/l/r/m-final types with "
                          "freq>=10 vs a frequency-matched (0.8-1.25x) unrelated partner of a "
                          f"different stem (seed {seed}), under two context representations.",
            "n_pairs": len(sib_pairs),
            "results": substitute,
        },
    )


def _word_contexts(c: Corpora, within_line: bool, top: int | None):
    keep = {w for w, _ in c.freq.most_common(top)} if top else None
    ctx = defaultdict(Counter)
    for s in ([L.tokens for L in c.lines] if within_line else [c.full]):
        for i, w in enumerate(s):
            for d, j in (("L", i - 1), ("R", i + 1)):
                if 0 <= j < len(s) and (keep is None or s[j] in keep):
                    ctx[w][d + ":" + s[j]] += 1
    return ctx


def claim_currier(c: Corpora) -> dict:
    counts = Counter((p.meta.get("L"), p.meta.get("H")) for p in c.pages.values())
    out = {}
    for lang in "AB":
        sub = filter_lines(c.lines, select_pages(c.pages, currier=lang))
        out[lang] = stem_preserving_terminal_permutation_test(terminal_records(sub))
    return result(
        "Currier A/B terminal-next-initial excess MI and language/hand page counts",
        {"A_excess": 0.0283, "B_excess": 0.0778, "A_p": 0.0033, "B_p": 0.0033,
         "A_hand1": 112, "B_hand2": 46, "B_hand3": 28, "B_hand5": 7, "A_hand3": 2},
        {"A_excess": out["A"]["excess_mi"], "B_excess": out["B"]["excess_mi"],
         "A_p": out["A"]["p"], "B_p": out["B"]["p"],
         "A_hand1": counts[("A", "1")], "B_hand2": counts[("B", "2")], "B_hand3": counts[("B", "3")],
         "B_hand5": counts[("B", "5")], "A_hand3": counts[("A", "3")]},
        "within_noise",
        "All P lines of pages with $L=A / $L=B; voynich_core stem-preserving test, 300 shuffles.",
        tests=out,
    )


# ---------------------------------------------------------------------------
# Hidden segmentation (section 6)
# ---------------------------------------------------------------------------

def _cuts(g: list[str], freq: Counter, thr: int = 5) -> list[int]:
    return [k for k in range(1, len(g))
            if freq["".join(g[:k])] >= thr and freq["".join(g[k:])] >= thr]


def claim_rare_decomposition(c: Corpora, null_reps: int = 20, seed: int = 20260925) -> dict:
    f = c.freq
    rare = sorted(w for w, n in f.items() if n <= 2 and len(eva_glyphs(w)) >= 6)
    dec = [w for w in rare if _cuts(eva_glyphs(w), f)]
    rng = random.Random(seed)
    null = []
    for _ in range(null_reps):
        hit = 0
        for w in rare:
            g = eva_glyphs(w); mid = g[1:-1]; rng.shuffle(mid)
            hit += bool(_cuts([g[0]] + mid + [g[-1]], f))
        null.append(hit / len(rare))
    by_thr = {thr: sum(bool(_cuts(eva_glyphs(w), f, thr)) for w in rare) / len(rare) for thr in (2, 3, 5, 10)}
    return result(
        "rare long forms decomposable into two frequent tokens, vs interior-shuffle null",
        {"rare_long_forms": 3250, "decomposable": 1661, "decomposable_pct": 51.1, "null_pct": 4.7},
        {"rare_long_forms": len(rare), "decomposable": len(dec),
         "decomposable_pct": 100 * len(dec) / len(rare), "null_pct": 100 * statistics.mean(null)},
        "exact",
        "Full corpus types with freq<=2 and >=6 EVA glyph units; decomposable if some cut "
        "(any position) gives two pieces each with corpus frequency >=5. Null shuffles "
        f"interior glyphs keeping first/last ({null_reps} reps, seed {seed}).",
        null_range_pct=[100 * min(null), 100 * max(null)],
        decomposable_pct_by_piece_threshold=by_thr,
        note="Null differs from 4.7% only by shuffle seed: means of 4.6-4.9% across seeds tried, single shuffles 3.9-5.2%.",
    )


def claim_cut_positions(c: Corpora) -> dict:
    f = c.freq
    rare = [w for w, n in f.items() if n <= 2 and len(eva_glyphs(w)) >= 6]
    tot = Counter(); hit = Counter()
    for w in rare:
        g = eva_glyphs(w)
        for k in range(1, len(g)):
            t = g[k - 1] in BOUNDARY_TERMINALS
            tot[t] += 1
            hit[t] += f["".join(g[:k])] >= 5 and f["".join(g[k:])] >= 5
    rt, ro = hit[True] / tot[True], hit[False] / tot[False]
    return result(
        "cut positions after n/l/r/m vs other glyphs yielding two frequent units",
        {"after_nlrm_pct": 51.8, "after_other_pct": 7.8, "rate_ratio": 6.62, "odds_ratio": 12.66},
        {"after_nlrm_pct": 100 * rt, "after_other_pct": 100 * ro, "rate_ratio": rt / ro,
         "odds_ratio": (rt / (1 - rt)) / (ro / (1 - ro))},
        "exact",
        "Every internal cut k=1..len-1 of the rare long forms above; hit if both pieces freq>=5.",
        counts={"nlrm_cuts": tot[True], "nlrm_hits": hit[True], "other_cuts": tot[False], "other_hits": hit[False]},
        note="Cuts within one word are not independent; the ratio is descriptive.",
    )


def claim_spaced_alternations(c: Corpora) -> dict:
    f = c.freq
    rare = [w for w, n in f.items() if n <= 2 and len(eva_glyphs(w)) >= 6]
    adj = Counter()
    for L in c.lines:
        adj.update(zip(L.tokens, L.tokens[1:]))
    n_dec = anyf = fo = ro = focc = rocc = 0
    for w in rare:
        g = eva_glyphs(w); ks = _cuts(g, f)
        if not ks:
            continue
        n_dec += 1
        F = [("".join(g[:k]), "".join(g[k:])) for k in ks]
        hf = any(adj[p] for p in F); hr = any(adj[(b, a)] for a, b in F)
        anyf += hf; fo += hf and not hr; ro += hr and not hf
        focc += sum(adj[p] for p in F); rocc += sum(adj[(b, a)] for a, b in F)
    return result(
        "decomposable rare forms with an exact spaced 'A B' realization; direction control",
        {"decomposable": 1661, "with_spaced": 359, "forward_only": 234, "reverse_only": 97, "occurrence_ratio": 1.66},
        {"decomposable": n_dec, "with_spaced": anyf, "forward_only": fo, "reverse_only": ro,
         "occurrence_ratio": focc / rocc},
        "exact",
        "Within-line adjacent pairs anywhere in the corpus; any valid cut of the joined form counts.",
        forward_occurrences=focc, reverse_occurrences=rocc,
    )


def claim_split_vs_unsplit(c: Corpora, boundary_bonus: float = 1.0) -> dict:
    variants = {}
    for neg in ("all_tokens", "tokens_len>=4", "tokens_with_candidate"):
        tp = fn = tn = fp = acc_n = acc_ok = 0
        for pid in c.herbal_pids:
            freq = Counter(w for L in c.herbal if L.page != pid for w in L.tokens)
            for L in (x for x in c.herbal if x.page == pid):
                for a, b in zip(L.tokens, L.tokens[1:]):
                    ga, gb = eva_glyphs(a), eva_glyphs(b)
                    if len(ga) < 2 or len(gb) < 2 or len(ga) + len(gb) > 14 or freq[a] < 2 or freq[b] < 2:
                        continue
                    cs = candidate_splits(a + b, freq, boundary_bonus=boundary_bonus)
                    if cs and cs[0]["llr"] > LLR_THRESHOLD:
                        tp += 1; acc_n += 1; acc_ok += cs[0]["k"] == len(ga)
                    else:
                        fn += 1
                for w in L.tokens:
                    if neg == "tokens_len>=4" and len(eva_glyphs(w)) < 4:
                        continue
                    cs = candidate_splits(w, freq, boundary_bonus=boundary_bonus)
                    if neg == "tokens_with_candidate" and not cs:
                        continue
                    if cs and cs[0]["llr"] > LLR_THRESHOLD:
                        fp += 1
                    else:
                        tn += 1
        se, sp = tp / (tp + fn), tn / (tn + fp)
        variants[neg] = {"positives": tp + fn, "negatives": tn + fp, "sensitivity": se,
                         "specificity": sp, "balanced_accuracy": (se + sp) / 2,
                         "accepted_boundary_accuracy": acc_ok / acc_n}
    v = variants["all_tokens"]
    return result(
        "split-vs-unsplit likelihood-ratio classifier on held-out pages",
        {"sensitivity": 0.839, "specificity": 0.916, "balanced_accuracy": 0.877, "accepted_boundary_accuracy": 0.993},
        {k: v[k] for k in ("sensitivity", "specificity", "balanced_accuracy", "accepted_boundary_accuracy")},
        "approximate",
        "Herbal-A/Hand-1, leave-one-page-out frequencies. Positives: held-out within-line "
        "pairs joined (script 02 filters, not restricted to ambiguous cases). Negatives: "
        f"every held-out written token. Split if best one-cut LLR > {LLR_THRESHOLD} "
        f"(boundary bonus {boundary_bonus}).",
        negative_class_variants=variants,
        note="The recorded threshold -2.1654 was reused, not re-learned; the original negative "
             "class and threshold-learning procedure are unknown. Real tokens may themselves be compounds.",
    )


# ---------------------------------------------------------------------------
# Information trajectory, vocabulary controls, entropy, lattices (8.3, 9-11)
# ---------------------------------------------------------------------------

def claim_information_trajectory(c: Corpora, collapse_reps: int = 40, seed: int = 7) -> dict:
    surface = c.herbal_tokens
    seg = c.lopo_segmented_herbal()
    norm = conservative_normalizer(seg)
    nz = [norm(x) for x in seg]
    surf_seeds = [permutation_corrected_adjacent_mi(surface, seed=s) for s in (12345, 1, 2)]
    k = len(set(nz))
    rng = random.Random(seed)
    collapsed = []
    for i in range(collapse_reps):
        types = sorted(set(seg)); rng.shuffle(types)
        m = {t: (j if j < k else rng.randrange(k)) for j, t in enumerate(types)}
        collapsed.append(permutation_corrected_adjacent_mi([m[t] for t in seg], reps=10, seed=i))
    collapsed.sort()
    lo, hi = collapsed[int(0.025 * collapse_reps)], collapsed[int(0.975 * collapse_reps) - 1]
    return result(
        "Herbal-A/Hand-1 adjacent-unit excess MI: surface -> segmented -> normalized, with random type-collapse control",
        {"types": [2468, 1991, 1640], "excess_mi": [0.0741, 0.0885, 0.1174],
         "random_collapse_mean": 0.0865, "random_collapse_95": [0.0813, 0.0925],
         "random_edge_pruning": 0.0486},
        {"types": [len(set(surface)), len(set(seg)), k],
         "excess_mi": [surf_seeds[0], permutation_corrected_adjacent_mi(seg), permutation_corrected_adjacent_mi(nz)],
         "random_collapse_mean": statistics.mean(collapsed), "random_collapse_95": [lo, hi],
         "random_edge_pruning": None},
        "within_noise",
        "Flattened Herbal-A/Hand-1 sequence. Segmented = viterbi_segment per token with "
        "leave-one-page-out frequencies (threshold -2.1654, bonus 1.0); normalized = "
        "conservative_normalizer on that. Excess MI = observed minus mean of 20 shuffles. "
        f"Control: random surjection of segmented types onto {k} classes ({collapse_reps} reps).",
        surface_excess_mi_by_seed=surf_seeds,
        note="Surface differs from 0.0741 only by shuffle seed (0.073-0.076). The edge-pruning "
             "control is not reconstructed: its definition is not recorded.",
    )


def claim_naibbe_trajectory(c: Corpora) -> dict:
    vals = {}
    for key, name in (("post", "naibbe_cipher_respaced.txt"), ("pre", "naibbe_cipher_pre.txt"),
                      ("plain", "naibbe_plain_units.txt")):
        t = [x.lower() for x in c.split_tokens(name)]
        vals[key] = [permutation_corrected_adjacent_mi(t, seed=s) for s in (12345, 1)]
    return result(
        "Naibbe adjacent-unit excess MI: post-deletion cipher, pre-deletion cipher, plaintext units",
        {"post": 0.0877, "pre": 0.0962, "plain": 0.6481},
        {k: v[0] for k, v in vals.items()},
        "within_noise",
        "Whole flattened file, permutation_corrected_adjacent_mi (20 shuffles).",
        by_seed=vals,
    )


def _cond_entropy(words: Sequence[str], order: int, glyph: bool) -> float:
    cond = Counter(); joint = Counter()
    for w in words:
        s = eva_glyphs(w) if glyph else list(w)
        for i in range(order, len(s)):
            ctx = tuple(s[i - order:i])
            joint[(ctx, s[i])] += 1; cond[ctx] += 1
    n = sum(joint.values())
    return -sum(v / n * math.log2(v / cond[ctx]) for (ctx, _), v in joint.items())


def claim_glyph_entropy(c: Corpora, window: int = 3000) -> dict:
    seg = c.lopo_segmented_herbal()
    norm = conservative_normalizer(seg)
    corpora = {
        "voynich_surface": (c.herbal_tokens, True),
        "voynich_normalized": ([norm(x) for x in seg], True),
        "naibbe": (c.split_tokens("naibbe_cipher_respaced.txt"), True),
        "latin": (c.text_words("latin_alfonsi.txt"), False),
        "italian": (c.text_words("italian_dante.txt"), False),
        "middle_high_german": (c.text_words("mhg_fh.txt"), False),
    }
    out = {}
    for name, (toks, glyph) in corpora.items():
        wins = [toks[i:i + window] for i in range(0, len(toks) - window + 1, window)]
        out[name] = {"windows": len(wins),
                     "H1": statistics.mean(_cond_entropy(w, 1, glyph) for w in wins),
                     "H2": statistics.mean(_cond_entropy(w, 2, glyph) for w in wins)}
    snap = {"voynich_surface": [2.219, 1.824], "voynich_normalized": [2.090, 1.628], "naibbe": [2.009, 1.675],
            "latin": [3.165, 2.408], "italian": [2.931, 2.259], "middle_high_german": [2.734, 1.702]}
    return result(
        "matched-window within-word conditional glyph entropy H(next|1), H(next|2)",
        snap, {k: [v["H1"], v["H2"]] for k, v in out.items()},
        "approximate",
        f"Non-overlapping {window}-token windows, averaged. Within-word transitions only (no "
        "boundary symbol). EVA compound glyph units for Voynich/Naibbe, Unicode letters for "
        "the natural-language texts (lower-cased, regex [^\\W\\d_]+).",
        windows={k: v["windows"] for k, v in out.items()},
        note="Voynich surface and Latin match within ~0.01 bits; other rows differ by up to "
             "~0.15. The ordering (Voynich/Naibbe ~2.0-2.2 vs Latin/Italian ~2.9-3.2 at H1) holds.",
    )


def claim_lattice_windows(c: Corpora, window: int = 6000) -> dict:
    seg = c.segmented_full()
    norm = conservative_normalizer(seg)
    corpora = {
        "voynich_normalized": ([norm(x) for x in seg], True),
        "naibbe": (c.split_tokens("naibbe_cipher_pre.txt"), True),
        "latin": (c.text_words("latin_alfonsi.txt"), False),
        "italian": (c.text_words("italian_dante.txt"), False),
        "middle_high_german": (c.text_words("mhg_fh.txt"), False),
    }
    out = {}
    for prefix_mode in ("eva_glyphs", "characters"):
        rows = {}
        for name, (toks, eva) in corpora.items():
            q, mx, top = [], [], Counter()
            for i in range(0, len(toks) - window + 1, window):
                L = prefix_remainder_lattices(toks[i:i + window], min_form_freq=5, min_shared_remainders=5,
                                              eva=eva and prefix_mode == "eva_glyphs")
                q.append(len(L)); mx.append(max((x["shared_remainders"] for x in L), default=0))
                top["/".join(L[0]["pair"]) if L else "none"] += 1
            rows[name] = {"windows": len(q), "mean_pairs": statistics.mean(q),
                          "mean_max_shared": statistics.mean(mx), "top_pair_counts": dict(top)}
        out[prefix_mode] = rows
    e = out["eva_glyphs"]
    return result(
        "prefix-pair lattices in matched 6000-token windows across corpora",
        {"voynich_pairs": 6.27, "voynich_max": 10.1, "naibbe_pairs": 6.9, "naibbe_max": 11.03,
         "latin_pairs": 0.1, "italian_pairs": 0.0, "mhg_pairs": 0.0, "ok_ot_top_in_every_voynich_window": True},
        {"voynich_pairs": e["voynich_normalized"]["mean_pairs"], "voynich_max": e["voynich_normalized"]["mean_max_shared"],
         "naibbe_pairs": e["naibbe"]["mean_pairs"], "naibbe_max": e["naibbe"]["mean_max_shared"],
         "latin_pairs": e["latin"]["mean_pairs"], "italian_pairs": e["italian"]["mean_pairs"],
         "mhg_pairs": e["middle_high_german"]["mean_pairs"]},
        "qualitative",
        "Non-overlapping windows; forms with freq>=5 in the window; 2-unit prefix; pairs sharing "
        ">=5 remainders. Voynich = whole-corpus segmented+normalized sequence.",
        by_prefix_mode=out,
        note="No single prefix definition reproduces both rows: EVA-glyph prefixes keep OK/OT on "
             "top for Voynich but give Naibbe ~3.8 pairs; character prefixes reproduce Naibbe "
             "(~7) but make ch/sh the top Voynich pair. Natural-language texts give ~0 either way. "
             "Italian and MHG files hold only one 6000-word window each.",
    )


# ---------------------------------------------------------------------------
# Naibbe positive control and OK/OT (sections 8, 12-14)
# ---------------------------------------------------------------------------

def _naibbe_aligned(c: Corpora) -> list[dict]:
    pre = c.token_lines("naibbe_cipher_pre.txt"); post = c.token_lines("naibbe_cipher_respaced.txt")
    out = []
    for li, (a, b) in enumerate(zip(pre, post)):
        i = 0
        for w in b:
            joined = ""; parts = []
            while i < len(a) and len(joined) < len(w):
                joined += a[i]; parts.append(a[i]); i += 1
            out.append({"line": li, "w": w, "parts": parts})
    return out


def claim_naibbe_localization(c: Corpora) -> dict:
    aligned = _naibbe_aligned(c)
    n_cand = n_true = ok = 0
    for fold in range(3):
        freq = Counter(x["w"] for x in aligned if x["line"] % 3 != fold)
        for r in aligned:
            if r["line"] % 3 != fold or len(r["parts"]) != 2:
                continue
            cs = candidate_splits(r["w"], freq, boundary_bonus=0.0)
            if not cs:
                continue
            tk = len(eva_glyphs(r["parts"][0]))
            n_cand += 1; n_true += any(x["k"] == tk for x in cs); ok += cs[0]["k"] == tk
    return result(
        "Naibbe boundary localization for two-part compounds (resolves 646 vs 634 discrepancy)",
        {"evaluable": 646, "accuracy": 0.9783},
        {"evaluable": n_cand, "correct": ok, "accuracy": ok / n_cand},
        "exact",
        "Script 04 setup (3 line-mod folds, min piece freq 2, no bonus). Denominator = two-part "
        "compounds with at least one candidate split; a top candidate at the wrong cut is an error.",
        script04_denominator=n_true, script04_accuracy=ok / n_true,
        note="Script 04 additionally drops the 12 compounds whose true cut is not among the "
             "candidates, giving 632/634. Both count the same 632 correct cases.",
    )


def claim_naibbe_compound_detection(c: Corpora, boundary_bonus: float = 0.0) -> dict:
    aligned = _naibbe_aligned(c)
    rows = []
    for fold in range(3):
        freq = Counter(x["w"] for x in aligned if x["line"] % 3 != fold)
        for r in aligned:
            if r["line"] % 3 != fold or len(r["parts"]) > 2:
                continue
            cs = candidate_splits(r["w"], freq, boundary_bonus=boundary_bonus)
            is_comp = len(r["parts"]) == 2
            rows.append((fold, is_comp, cs[0]["llr"] if cs else None,
                         cs[0]["k"] == len(eva_glyphs(r["parts"][0])) if cs and is_comp else None))

    def se_sp(rs, t):
        P = [r for r in rs if r[1]]; N = [r for r in rs if not r[1]]
        se = sum(r[2] is not None and r[2] > t for r in P) / len(P)
        sp = sum(not (r[2] is not None and r[2] > t) for r in N) / len(N)
        return se, sp

    out = {}
    for universe in ("tokens_with_candidate", "all_tokens"):
        R = [r for r in rows if universe == "all_tokens" or r[2] is not None]
        baccs = []; acc = [0, 0]
        for fold in range(3):
            tr = [r for r in R if r[0] != fold]; te = [r for r in R if r[0] == fold]
            grid = sorted({round(r[2], 2) for r in tr if r[2] is not None})
            best = max(grid, key=lambda t: sum(se_sp(tr, t)))
            baccs.append(sum(se_sp(te, best)) / 2)
            for r in te:
                if r[1] and r[2] is not None and r[2] > best:
                    acc[0] += 1; acc[1] += r[3]
        out[universe] = {"n": len(R), "cv_balanced_accuracy": statistics.mean(baccs),
                         "accepted_boundary_accuracy": acc[1] / acc[0]}
    p = out["tokens_with_candidate"]
    return result(
        "Naibbe compound-vs-single detection and accepted-boundary accuracy",
        {"balanced_accuracy": 0.827, "accepted_boundary_accuracy": 0.996},
        {"balanced_accuracy": p["cv_balanced_accuracy"], "accepted_boundary_accuracy": p["accepted_boundary_accuracy"]},
        "approximate",
        "Script 04 folds; score = best one-cut LLR; threshold chosen on the two training folds "
        "to maximise balanced accuracy, applied to the test fold. Universe = single and two-part "
        "tokens with at least one candidate split (3+-part compounds excluded).",
        universes=out,
    )


def _cmi(recs):
    by = defaultdict(list)
    for r, p, ctx in recs:
        by[r].append((p, ctx))
    n = len(recs)
    return sum(len(v) / n * mutual_information_pairs(v) for v in by.values())


def residual_context_test(recs, reps: int = 300, seed: int = 1) -> dict:
    """I(prefix; right context | remainder), null shuffles prefix within remainder."""
    obs = _cmi(recs)
    rng = random.Random(seed)
    groups = defaultdict(list)
    for i, (r, _, _) in enumerate(recs):
        groups[r].append(i)
    nulls = []
    for _ in range(reps):
        P = [p for _, p, _ in recs]
        for idx in groups.values():
            v = [P[i] for i in idx]; rng.shuffle(v)
            for i, x in zip(idx, v):
                P[i] = x
        nulls.append(_cmi([(r, p, ctx) for (r, _, ctx), p in zip(recs, P)]))
    return {"n": len(recs), "observed": obs, "excess": obs - statistics.mean(nulls),
            "p": (1 + sum(x >= obs for x in nulls)) / (reps + 1)}


def _okot_records(seq, rems, ctxf):
    return [(w[2:], w[:2], ctxf(seq[i + 1])) for i, w in enumerate(seq[:-1])
            if w[:2] in ("ok", "ot") and w[2:] in rems]


def claim_okot_context(c: Corpora, top_context: int = 100, min_support: int = 20) -> dict:
    cip = c.split_tokens("naibbe_cipher_pre.txt"); plain = c.split_tokens("naibbe_plain_units.txt")
    lab = defaultdict(Counter)
    for x, p in zip(cip, plain):
        lab[x][p] += 1
    top = {x: v.most_common(1)[0][0] for x, v in lab.items()}
    f = Counter(cip)
    pairs = [w[2:] for w in f if w.startswith("ok") and len(w) > 2 and f[w] >= 5 and f["ot" + w[2:]] >= 5]
    same = {r for r in pairs if top["ok" + r] == top["ot" + r]}; diff = set(pairs) - same
    keep = {w for w, _ in f.most_common(top_context)}
    ctxf = lambda x: x if x in keep else "*"
    naibbe = {"same_plaintext": residual_context_test(_okot_records(cip, same, ctxf)),
              "different_plaintext": residual_context_test(_okot_records(cip, diff, ctxf))}

    seg = c.segmented_full(); norm = conservative_normalizer(seg); vn = [norm(x) for x in seg]
    fv = Counter(vn); keepv = {w for w, _ in fv.most_common(top_context)}
    ctxv = lambda x: x if x in keepv else "*"
    rems = sorted(w[2:] for w in fv if w.startswith("ok") and len(w) > 2
                  and fv[w] >= min_support and fv["ot" + w[2:]] >= min_support)
    voy = {"pooled": residual_context_test(_okot_records(vn, set(rems), ctxv)),
           "oko_oto": residual_context_test(_okot_records(vn, {"o"}, ctxv), reps=999)}
    for r in ("cho", "chy", "eo", "sho"):
        voy["ok" + r + "_ot" + r] = residual_context_test(_okot_records(vn, {r}, ctxv))
    return result(
        "OK/OT residual right-context information after conditioning on remainder",
        {"naibbe_same_excess": -0.0005, "naibbe_same_p": 0.505, "naibbe_diff_excess": 0.0305,
         "naibbe_diff_p": 0.0033, "voynich_pooled_excess": 0.038, "voynich_pooled_p": 0.012,
         "voynich_oko_oto_excess": 0.145, "voynich_oko_oto_p": 0.001},
        {"naibbe_same_excess": naibbe["same_plaintext"]["excess"], "naibbe_same_p": naibbe["same_plaintext"]["p"],
         "naibbe_diff_excess": naibbe["different_plaintext"]["excess"], "naibbe_diff_p": naibbe["different_plaintext"]["p"],
         "voynich_pooled_excess": voy["pooled"]["excess"], "voynich_pooled_p": voy["pooled"]["p"],
         "voynich_oko_oto_excess": voy["oko_oto"]["excess"], "voynich_oko_oto_p": voy["oko_oto"]["p"]},
        "qualitative",
        "Statistic: sum_r P(r) MI(prefix; next token | remainder r), next token kept if among the "
        f"top {top_context} types else '*'. Null shuffles ok/ot within remainder (300 reps; 999 for "
        "OKO/OTO). Naibbe: pre-respacing cipher, 32 OK/OT pairs (both forms freq>=5), split by "
        "majority plaintext label. Voynich: whole-corpus segmented+normalized sequence, "
        f"remainders with both forms freq>={min_support}.",
        naibbe=naibbe, voynich=voy, voynich_remainders=rems,
        note="Pattern reproduced (Naibbe true homophones ~0 and n.s.; different-plaintext and "
             "Voynich pooled significant; OKO/OTO strongest; cho/chy/eo/sho null) but excess sizes "
             "differ and are not comparable across different sample sizes.",
    )


def claim_naibbe_context_homophones(c: Corpora, min_freq: int = 20, top_context: int = 200) -> dict:
    cip = c.split_tokens("naibbe_cipher_pre.txt"); plain = c.split_tokens("naibbe_plain_units.txt")
    f = Counter(cip); lab = defaultdict(Counter)
    for x, p in zip(cip, plain):
        lab[x][p] += 1
    top = {x: v.most_common(1)[0][0] for x, v in lab.items()}
    T = [w for w, n in f.items() if n >= min_freq]
    ctx = context_vectors(cip, top_context=top_context)
    same, diff = [], []
    elig = nn = t5 = 0
    for i, a in enumerate(T):
        sims = sorted(((cosine_counts(ctx[a], ctx[b]), top[a] == top[b]) for b in T if b != a), reverse=True)
        for b in T[i + 1:]:
            (same if top[a] == top[b] else diff).append(cosine_counts(ctx[a], ctx[b]))
        if any(s for _, s in sims):
            elig += 1; nn += sims[0][1]; t5 += any(s for _, s in sims[:5])
    neg = sorted(diff)
    auc = sum(bisect_left(neg, x) + 0.5 * (bisect_right(neg, x) - bisect_left(neg, x)) for x in same) / (len(same) * len(neg))
    return result(
        "Naibbe context-only homophone recovery",
        {"frequent_types": 178, "eligible": 152, "same_median": 0.964, "diff_median": 0.921,
         "auc": 0.748, "nn_rate": 0.329, "top5_rate": 0.474},
        {"frequent_types": len(T), "eligible": elig, "same_median": statistics.median(same),
         "diff_median": statistics.median(diff), "auc": auc, "nn_rate": nn / elig, "top5_rate": t5 / elig},
        "exact",
        f"Pre-respacing cipher types with freq>={min_freq}; context_vectors(top={top_context}) over the "
        "flattened stream; label = majority plaintext unit (evaluation only). AUC over all type pairs.",
    )


# ---------------------------------------------------------------------------
# f3r / entry starts (section 16)
# ---------------------------------------------------------------------------

def claim_first_token_uniqueness(c: Corpora) -> dict:
    first = {}
    for L in c.herbal:
        first.setdefault(L.page, L.tokens[0])
    def uniq(vals):
        n = Counter(vals); return 100 * sum(n[v] == 1 for v in vals) / len(vals)
    fs = Counter(c.herbal_tokens)
    seg_all = [p for w in c.herbal_tokens for p in viterbi_segment(w, fs)["parts"]]
    norm = conservative_normalizer(seg_all)
    fseg = Counter(seg_all)
    def gall(x, freq):
        return x[1:] if x[:1] in "tkpf" and len(x) > 2 and freq[x[1:]] >= 2 else x
    firsts = [viterbi_segment(w, fs)["parts"][0] for w in first.values()]
    fnorm = Counter(norm(x) for x in seg_all)
    variants = {
        "segmented_first_unit": uniq(firsts),
        "normalized": uniq([norm(x) for x in firsts]),
        "gallows_then_normalized": uniq([norm(gall(x, fseg)) for x in firsts]),
        "normalized_then_gallows": uniq([gall(norm(x), fnorm) for x in firsts]),
    }
    return result(
        "Herbal-A/Hand-1 page-first tokens unique among the 95 page starts",
        {"raw_pct": 87.4, "latent_pct": 70.5},
        {"raw_pct": uniq(list(first.values())),
         "latent_pct_range": [min(v for k, v in variants.items() if k != "segmented_first_unit"),
                              max(v for k, v in variants.items() if k != "segmented_first_unit")]},
        "approximate",
        "First token of each page's first P line; unique = occurs once among the 95 first tokens. "
        "Latent: first Viterbi unit (subset frequencies), conservative_normalizer, optional removal "
        "of an initial t/k/p/f gallows when the remainder is attested.",
        latent_variants=variants,
        note="Raw value is exact. 'Conservative gallows handling' is not specified; tried variants "
             "give 67-75%, bracketing the recorded 70.5%.",
    )


ALL_CLAIMS: dict[str, Callable[[Corpora], dict]] = {
    "m_line_final": claim_m_line_final,
    "internal_m_sibling": claim_internal_m_sibling,
    "rl_families": claim_rl_families,
    "context_cosines": claim_context_cosines,
    "currier": claim_currier,
    "rare_decomposition": claim_rare_decomposition,
    "cut_positions": claim_cut_positions,
    "spaced_alternations": claim_spaced_alternations,
    "split_vs_unsplit": claim_split_vs_unsplit,
    "information_trajectory": claim_information_trajectory,
    "naibbe_trajectory": claim_naibbe_trajectory,
    "glyph_entropy": claim_glyph_entropy,
    "lattice_windows": claim_lattice_windows,
    "naibbe_localization": claim_naibbe_localization,
    "naibbe_compound_detection": claim_naibbe_compound_detection,
    "okot_context": claim_okot_context,
    "naibbe_context_homophones": claim_naibbe_context_homophones,
    "first_token_uniqueness": claim_first_token_uniqueness,
}

# Claims that depend on the ZL3b parser and are cheap enough to rerun with the
# corrected alternative-reading handling as a sensitivity check.
PARSER_SENSITIVE = ("internal_m_sibling", "rl_families", "rare_decomposition", "cut_positions",
                    "spaced_alternations", "m_line_final", "currier")
