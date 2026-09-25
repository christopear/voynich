"""Pairwise 'same hidden unit?' features, validation and clustering (CONTINUATION §19).

Specification: EQUIVALENCE_PROTOCOL.md. Every corpus is reduced to token lines
(lists of str, with None for an unreadable/uncertain token) and processed
identically. Labels are used only as targets and for grouped fold assignment.
"""
from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (adjusted_rand_score, average_precision_score, brier_score_loss,
                             precision_recall_curve, roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from voynich_core import eva_glyphs

SEED = 20260925
MIN_FREQ = 20
TOP_CONTEXT = 200
TERMINALS = set("nlrm")

FEATURE_GROUPS = {
    "context": ["cos_lr", "cos_left", "cos_right", "cos_left_nocatch", "cos_right_nocatch",
                "js_next_initial", "js_prev_final"],
    "frequency": ["log_fmin", "log_fmax", "abs_log_ratio"],
    "form": ["edit", "edit_norm", "len_diff", "common_prefix", "common_suffix", "same_first",
             "same_first2", "same_rem1", "same_rem2", "same_last", "terminal_alternation"],
    "position": ["d_line_initial", "d_line_final"],
}
PRIMARY_GROUPS = ("context", "frequency", "form")


def features_of(groups=PRIMARY_GROUPS) -> list[str]:
    return [f for g in groups for f in FEATURE_GROUPS[g]]


# ---------------------------------------------------------------------------
# Corpus statistics
# ---------------------------------------------------------------------------

@dataclass
class Corpus:
    name: str
    lines: list[list[str | None]]
    min_freq: int = MIN_FREQ
    freq: Counter = field(init=False)
    types: list[str] = field(init=False)

    def __post_init__(self):
        self.freq = Counter(w for ln in self.lines for w in ln if w)
        self.types = sorted(w for w, n in self.freq.items() if n >= self.min_freq)
        self._stats()

    def _stats(self):
        idx = {w: i for i, w in enumerate(self.types)}
        top = [w for w, _ in self.freq.most_common(TOP_CONTEXT)]
        dims = {w: j for j, w in enumerate(top + ["^", "$", "*"])}
        self.catch = dims["*"]
        glyphs = sorted({g for w in self.freq for g in eva_glyphs(w)} | {"^", "$"})
        gdim = {g: j for j, g in enumerate(glyphs)}
        T = len(self.types)
        self.L = np.zeros((T, len(dims))); self.R = np.zeros((T, len(dims)))
        self.next_initial = np.zeros((T, len(glyphs))); self.prev_final = np.zeros((T, len(glyphs)))
        self.line_initial = np.zeros(T); self.line_final = np.zeros(T)
        counts = np.zeros(T)
        for ln in self.lines:
            for k, w in enumerate(ln):
                i = idx.get(w)
                if i is None:
                    continue
                counts[i] += 1
                # Missing readings are gaps: never bridged, never recorded.
                if k == 0:
                    self.L[i, dims["^"]] += 1; self.prev_final[i, gdim["^"]] += 1; self.line_initial[i] += 1
                elif ln[k - 1]:
                    self.L[i, dims.get(ln[k - 1], self.catch)] += 1
                    self.prev_final[i, gdim[eva_glyphs(ln[k - 1])[-1]]] += 1
                if k == len(ln) - 1:
                    self.R[i, dims["$"]] += 1; self.next_initial[i, gdim["$"]] += 1; self.line_final[i] += 1
                elif ln[k + 1]:
                    self.R[i, dims.get(ln[k + 1], self.catch)] += 1
                    self.next_initial[i, gdim[eva_glyphs(ln[k + 1])[0]]] += 1
        self.line_initial /= np.maximum(counts, 1); self.line_final /= np.maximum(counts, 1)

    def pairs(self) -> list[tuple[int, int]]:
        T = len(self.types)
        return [(i, j) for i in range(T) for j in range(i + 1, T)]

    def feature_matrix(self, pairs=None) -> tuple[np.ndarray, list[str]]:
        pairs = self.pairs() if pairs is None else pairs
        I = np.array([p[0] for p in pairs]); J = np.array([p[1] for p in pairs])
        names = features_of(tuple(FEATURE_GROUPS))
        cols = {}
        LR = np.hstack([self.L, self.R])
        nocatch = np.ones(self.L.shape[1]); nocatch[self.catch] = 0
        for key, M in (("cos_lr", LR), ("cos_left", self.L), ("cos_right", self.R),
                       ("cos_left_nocatch", self.L * nocatch), ("cos_right_nocatch", self.R * nocatch)):
            cols[key] = _cosine_rows(M, I, J)
        cols["js_next_initial"] = _js_rows(self.next_initial, I, J)
        cols["js_prev_final"] = _js_rows(self.prev_final, I, J)
        f = np.array([self.freq[w] for w in self.types], dtype=float)
        cols["log_fmin"] = np.log(np.minimum(f[I], f[J])); cols["log_fmax"] = np.log(np.maximum(f[I], f[J]))
        cols["abs_log_ratio"] = np.abs(np.log(f[I]) - np.log(f[J]))
        cols["d_line_initial"] = np.abs(self.line_initial[I] - self.line_initial[J])
        cols["d_line_final"] = np.abs(self.line_final[I] - self.line_final[J])
        g = [tuple(eva_glyphs(w)) for w in self.types]
        form = np.array([form_features(g[i], g[j]) for i, j in pairs], dtype=float)
        for k, key in enumerate(FEATURE_GROUPS["form"]):
            cols[key] = form[:, k]
        return np.column_stack([cols[n] for n in names]), names


def _cosine_rows(M, I, J):
    norm = np.linalg.norm(M, axis=1); norm[norm == 0] = 1
    U = M / norm[:, None]
    return np.einsum("ij,ij->i", U[I], U[J])


def _js_rows(M, I, J):
    P = M / np.maximum(M.sum(1, keepdims=True), 1)
    a, b = P[I], P[J]; m = (a + b) / 2
    def kl(x, y):
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(x > 0, x * np.log2(x / np.where(y > 0, y, 1)), 0).sum(1)
    return (kl(a, m) + kl(b, m)) / 2


def edit_distance(a, b) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def form_features(a: tuple, b: tuple) -> list[float]:
    ed = edit_distance(a, b)
    cp = 0
    while cp < min(len(a), len(b)) and a[cp] == b[cp]:
        cp += 1
    cs = 0
    while cs < min(len(a), len(b)) and a[-1 - cs] == b[-1 - cs]:
        cs += 1
    term = a[-1] in TERMINALS and b[-1] in TERMINALS and a[:-1] == b[:-1] and a[-1] != b[-1]
    return [ed, ed / max(len(a), len(b)), abs(len(a) - len(b)), cp, cs,
            a[0] == b[0], a[:2] == b[:2],
            len(a) > 1 and len(b) > 1 and a[1:] == b[1:],
            len(a) > 2 and len(b) > 2 and a[2:] == b[2:],
            a[-1] == b[-1], term]


def select(X, names, groups) -> np.ndarray:
    keep = set(features_of(groups))
    return X[:, [k for k, n in enumerate(names) if n in keep]]


# ---------------------------------------------------------------------------
# Models and metrics
# ---------------------------------------------------------------------------

def make_model(kind: str):
    if kind == "logistic":
        return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))
    if kind == "boosting":
        return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
                                              l2_regularization=1.0, random_state=SEED)
    raise ValueError(kind)


def assign_folds(values, k=5, seed=SEED) -> dict:
    vals = sorted(set(values)); random.Random(seed).shuffle(vals)
    return {v: i % k for i, v in enumerate(vals)}


def grouped_cv(pairs, y, X, type_group: list, kind: str, k: int = 5):
    """Out-of-fold probabilities; a pair is tested only when both types share the fold."""
    folds = assign_folds(type_group, k)
    fa = np.array([folds[type_group[i]] for i, _ in pairs]); fb = np.array([folds[type_group[j]] for _, j in pairs])
    p = np.full(len(pairs), np.nan); fold_of = np.full(len(pairs), -1)
    for f in range(k):
        tr = (fa != f) & (fb != f); te = (fa == f) & (fb == f)
        model = make_model(kind).fit(X[tr], y[tr])
        p[te] = model.predict_proba(X[te])[:, 1]; fold_of[te] = f
    return p, fold_of


def metrics(y, p, pairs, n_types=None) -> dict:
    y = np.asarray(y); p = np.asarray(p)
    prec, rec, _ = precision_recall_curve(y, p)
    def recall_at(pr):
        ok = rec[prec >= pr]; return float(ok.max()) if len(ok) else 0.0
    def precision_at(rc):
        ok = prec[rec >= rc]; return float(ok.max()) if len(ok) else 0.0
    out = {"n_pairs": int(len(y)), "positives": int(y.sum()), "prevalence": float(y.mean()),
           "roc_auc": float(roc_auc_score(y, p)), "pr_auc": float(average_precision_score(y, p)),
           "recall_at_precision_0.5": recall_at(0.5), "recall_at_precision_0.8": recall_at(0.8),
           "precision_at_recall_0.25": precision_at(0.25), "precision_at_recall_0.5": precision_at(0.5)}
    if 0 <= p.min() and p.max() <= 1:
        out["brier"] = float(brier_score_loss(y, p))
        edges = np.quantile(p, np.linspace(0, 1, 11)); b = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, 9)
        out["reliability"] = [{"bin": int(k), "mean_p": float(p[b == k].mean()), "observed": float(y[b == k].mean()),
                               "n": int((b == k).sum())} for k in range(10) if (b == k).any()]
    out.update(retrieval(y, p, pairs))
    return out


def retrieval(y, p, pairs) -> dict:
    nb = defaultdict(list)
    for (i, j), yy, pp in zip(pairs, y, p):
        nb[i].append((pp, yy)); nb[j].append((pp, yy))
    elig = [v for v in nb.values() if any(yy for _, yy in v)]
    if not elig:
        return {}
    nn = sum(sorted(v, key=lambda t: -t[0])[0][1] for v in elig)
    t5 = sum(any(yy for _, yy in sorted(v, key=lambda t: -t[0])[:5]) for v in elig)
    return {"retrieval_types": len(elig), "nearest_neighbour_rate": nn / len(elig), "top5_rate": t5 / len(elig)}


def type_bootstrap(y, p, pairs, reps=500, seed=SEED) -> dict:
    y = np.asarray(y); p = np.asarray(p)
    types = sorted({t for pr in pairs for t in pr})
    I = np.array([a for a, _ in pairs]); J = np.array([b for _, b in pairs])
    pos = {t: k for k, t in enumerate(types)}; I = np.array([pos[a] for a in I]); J = np.array([pos[b] for b in J])
    rng = np.random.default_rng(seed); auc = []; ap = []
    for _ in range(reps):
        m = np.bincount(rng.integers(0, len(types), len(types)), minlength=len(types)).astype(float)
        w = m[I] * m[J]
        if w[y == 1].sum() == 0 or w[y == 0].sum() == 0:
            continue
        auc.append(roc_auc_score(y, p, sample_weight=w)); ap.append(average_precision_score(y, p, sample_weight=w))
    q = lambda v: [float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))]
    return {"reps": len(auc), "roc_auc_95": q(auc), "pr_auc_95": q(ap)}


def cluster(n_types: int, pairs, p, threshold=0.5) -> np.ndarray:
    D = np.ones((n_types, n_types)); np.fill_diagonal(D, 0)
    for (i, j), pp in zip(pairs, p):
        D[i, j] = D[j, i] = 1 - pp
    if n_types < 2:
        return np.ones(n_types, dtype=int)
    return fcluster(linkage(squareform(D, checks=False), "average"), t=1 - threshold, criterion="distance")


def cluster_scores(labels_true, labels_pred) -> dict:
    n = len(labels_true); tp = fp = fn = 0
    for i in range(n):
        for j in range(i + 1, n):
            s, t = labels_pred[i] == labels_pred[j], labels_true[i] == labels_true[j]
            tp += s and t; fp += s and not t; fn += t and not s
    P = tp / (tp + fp) if tp + fp else 0.0; R = tp / (tp + fn) if tp + fn else 0.0
    return {"pair_precision": P, "pair_recall": R, "pair_f1": 2 * P * R / (P + R) if P + R else 0.0,
            "ari": float(adjusted_rand_score(labels_true, labels_pred)),
            "clusters": int(len(set(labels_pred))), "true_classes": int(len(set(labels_true)))}


def high_probability_summary(corpus: Corpus, p, pairs) -> dict:
    T = len(corpus.types); p = np.asarray(p)
    sizes = Counter(Counter(cluster(T, pairs, p)).values())
    return {"types": T, "pairs": len(pairs),
            "pairs_p_ge_0.5": int((p >= 0.5).sum()), "pairs_p_ge_0.8": int((p >= 0.8).sum()),
            "pairs_p_ge_0.5_per_type": float((p >= 0.5).sum() / T),
            "rate_p_ge_0.5": float((p >= 0.5).mean()), "rate_p_ge_0.8": float((p >= 0.8).mean()),
            "mean_top100_p": float(np.sort(p)[-100:].mean()),
            "cluster_size_counts_at_0.5": {int(k): int(v) for k, v in sorted(sizes.items())}}
