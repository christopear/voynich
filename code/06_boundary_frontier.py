"""Prospective boundary/layout extension. See FRONTIER_PROTOCOL.md.

Run: uv run python code/06_boundary_frontier.py
All model fits are CPU-only and all inputs local. Original analyses are unchanged.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression

from voynich_core import eva_glyphs

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/frontier_2026-09-24"
SEED = 20260924
CLASSES = "nlr"


def token(raw):
    uncertain = bool(re.search(r"[?*\[\]{}'’@]", raw))
    clean = re.sub(r"\[([^:\]]*):[^\]]*\]", r"\1", raw)
    clean = clean.replace("{", "").replace("}", "").replace("'", "").replace("’", "")
    return {"word": clean, "clean": not uncertain and bool(re.fullmatch("[a-z]+", clean))}


def parse_body(body):
    body = re.sub(r"<!.*?>", "", body)
    body = re.sub(r"<@[^>]*>", "", body)
    body = body.replace("<%>", "").replace("<$>", "").replace("<~>", "")
    # A separator remains at its original position even when its neighbour is bad.
    parts = re.split(r"(<->|[.,])", body.strip().rstrip("-= "))
    words = [token(p.strip()) for p in parts[::2]]
    gaps = [{".": "ordinary", ",": "uncertain", "<->": "drawing"}[p] for p in parts[1::2]]
    return words, gaps


def load_lines(path):
    meta, lines = {}, []
    for raw in path.read_text().splitlines():
        hm = re.match(r"^<(f[^.> ]+)>\s*<!([^>]*)>", raw)
        if hm:
            meta[hm[1]] = dict(re.findall(r"\$(\w)=([^\s>]+)", hm[2]))
        lm = re.match(r"^<(f[^.>]+)\.(\d+),([^>]*)>\s*(.*)$", raw)
        if not lm or lm[3][1:] != "P0":
            continue
        # IVTFF inline variable changes persist until another change on that page.
        current = dict(meta.get(lm[1], {}))
        for change in re.findall(r"<@([^>]*)>", lm[4]):
            current.update(re.findall(r"(\w)=([^\s>]+)", change))
        meta[lm[1]] = current
        words, gaps = parse_body(lm[4])
        lines.append(dict(page=lm[1], folio=re.match(r"f\d+", lm[1])[0],
                          number=int(lm[2]), locus=f"{lm[1]}.{lm[2]}",
                          paragraph_start="<%>" in lm[4], paragraph_end="<$>" in lm[4],
                          words=words, gaps=gaps, meta=dict(current)))
    return lines


def record(line, index, left, right, kind):
    stem = left[:-1]
    return dict(id=f"{line['locus']}:{index}:{kind}", page=line["page"], folio=line["folio"],
                locus=line["locus"], index=index, stem=stem, terminal=left[-1], left=left,
                right=right, initial=eva_glyphs(right)[0], kind=kind,
                position=index / max(1, len(line["words"]) - 1),
                paragraph_start=line["paragraph_start"],
                hand=line["meta"].get("H", "?"), currier=line["meta"].get("L", "?"),
                section=line["meta"].get("I", "?"))


def valid_pair(left, right):
    return left["clean"] and right["clean"] and len(eva_glyphs(left["word"])) >= 2 and left["word"][-1] in CLASSES


def observations(lines):
    rows = []
    for j, line in enumerate(lines):
        for i, kind in enumerate(line["gaps"]):
            left, right = line["words"][i:i+2]
            if valid_pair(left, right):
                rows.append(record(line, i, left["word"], right["word"], kind))
        if j + 1 == len(lines):
            continue
        nxt = lines[j+1]
        if line["page"] != nxt["page"] or nxt["number"] != line["number"] + 1:
            continue
        left, right = line["words"][-1], nxt["words"][0]
        if valid_pair(left, right):
            kind = "paragraph" if line["paragraph_end"] or nxt["paragraph_start"] else "line"
            rows.append(record(line, len(line["words"])-1, left["word"], right["word"], kind))
    return rows


def assign_folds(values):
    values = sorted(set(values))
    np.random.default_rng(SEED).shuffle(values)
    return {v: i % 5 for i, v in enumerate(values)}


def features(row, context=False, identity=False, geometry=False, boundary=False):
    g = eva_glyphs(row["stem"])
    suffix = "|".join(g[-2:])
    d = {"length": str(min(len(g), 12)), "prefix1": g[0], "prefix2": "|".join(g[:2]),
         "suffix1": g[-1], "suffix2": suffix, "hand": row["hand"],
         "currier": row["currier"], "section": row["section"],
         "position": row["position"], "paragraph_start": float(row["paragraph_start"])}
    d.update({f"count:{k}": float(v) for k, v in Counter(g).items()})
    if identity:
        d["stem"] = row["stem"]
    if context:
        initial = row["initial"]
        d.update(initial=initial, suffix_initial=f"{suffix}/{initial}",
                 last_initial=f"{g[-1]}/{initial}", hand_initial=f"{row['hand']}/{initial}")
        if identity:
            d["stem_initial"] = f"{row['stem']}/{initial}"
    if boundary:
        d["kind"] = row["kind"]
        d["kind_suffix"] = row["kind"] + "/" + suffix
        if context:
            d["kind_initial"] = row["kind"] + "/" + row["initial"]
    if geometry:
        d["x_start"] = row["x_start"]
        d["x_bin"] = str(min(9, max(0, int(row["x_start"] * 10))))
    return d


class Model:
    def __init__(self, rows, **spec):
        self.spec = spec
        self.vectorizer = DictVectorizer()
        x = self.vectorizer.fit_transform([features(r, **spec) for r in rows])
        self.model = LogisticRegression(C=1, max_iter=1200, solver="lbfgs", tol=1e-6)
        self.model.fit(x, [r["terminal"] for r in rows])
        self.classes = [list(self.model.classes_).index(c) for c in CLASSES]

    def predict(self, rows):
        x = self.vectorizer.transform([features(r, **self.spec) for r in rows])
        return self.model.predict_proba(x)[:, self.classes]


def score(rows, p0, p1, experiment, fold):
    out = []
    for row, a, b in zip(rows, p0, p1):
        y = CLASSES.index(row["terminal"])
        onehot = np.eye(3)[y]
        r = dict(row, experiment=experiment, fold=fold,
                 loss0=float(-np.log2(max(a[y], 1e-12))), loss1=float(-np.log2(max(b[y], 1e-12))),
                 correct0=int(a.argmax() == y), correct1=int(b.argmax() == y),
                 brier0=float(sum((a-onehot)**2)), brier1=float(sum((b-onehot)**2)))
        r.update({f"p{m}_{c}": float(p[k]) for m, p in enumerate((a,b)) for k,c in enumerate(CLASSES)})
        out.append(r)
    return out


def cluster_ci(rows, field0, field1, cluster):
    groups = defaultdict(list)
    for r in rows:
        groups[r[cluster]].append(r[field0] - r[field1])
    if len(groups) < 2:
        return None
    sums = np.array([sum(v) for v in groups.values()])
    ns = np.array([len(v) for v in groups.values()])
    rng = np.random.default_rng(SEED)
    estimates = []
    for _ in range(2000):
        i = rng.integers(len(ns), size=len(ns))
        estimates.append(float(sums[i].sum()/ns[i].sum()))
    return np.quantile(estimates, [.025, .975]).tolist()


def summary(rows):
    if not rows:
        return {"n": 0}
    d = dict(n=len(rows), folios=len({r["folio"] for r in rows}), stems=len({r["stem"] for r in rows}),
             loss_base=float(np.mean([r["loss0"] for r in rows])),
             loss_full=float(np.mean([r["loss1"] for r in rows])),
             accuracy_base=float(np.mean([r["correct0"] for r in rows])),
             accuracy_full=float(np.mean([r["correct1"] for r in rows])),
             brier_base=float(np.mean([r["brier0"] for r in rows])),
             brier_full=float(np.mean([r["brier1"] for r in rows])))
    d["gain_bits"] = d["loss_base"] - d["loss_full"]
    for cluster in ("folio", "stem"):
        d[f"gain_ci_{cluster}"] = cluster_ci(rows, "loss0", "loss1", cluster)
    d["gain_by_fold"] = {str(f):float(np.mean([r["loss0"]-r["loss1"] for r in rows if r["fold"] == f])) for f in sorted({r["fold"] for r in rows})}
    return d


def hidden_candidates(train_lines, test_lines):
    freq = Counter(w["word"] for ln in train_lines for w in ln["words"] if w["clean"])
    candidates, seen = [], set()
    for line in test_lines:
        for i, word in enumerate(line["words"]):
            joined = word["word"]
            if not word["clean"] or joined in seen or freq[joined] > 2:
                continue
            seen.add(joined)
            g = eva_glyphs(joined)
            if len(g) < 6:
                continue
            options = []
            for cut in range(2, len(g)-1):
                left, right = "".join(g[:cut]), "".join(g[cut:])
                if left[-1] not in CLASSES:
                    continue
                pooled = sum(freq[left[:-1]+t] for t in CLASSES)
                if pooled >= 5 and freq[right] >= 5:
                    options.append((pooled*freq[right], cut, left, right, pooled))
            if options:
                _, cut, left, right, pooled = max(options, key=lambda x: (x[0], -x[1]))
                r = record(line, i, left, right, "hidden")
                r.update(joined=joined, cut=cut, pooled_freq=pooled, right_freq=freq[right], train_joined_freq=freq[joined])
                candidates.append(r)
    return candidates


def attach_coordinates(lines, rows):
    bypage = defaultdict(list)
    for line in lines:
        bypage[line["page"]].extend((line, i, w) for i,w in enumerate(line["words"]))
    lookup, audit = {}, []
    for path in sorted((ROOT/"data/frontier/boxes").glob("*.js")):
        text = bypage.get(path.stem, [])
        if not text:
            continue
        vocab, boxes = json.loads(path.read_text())
        visual = [vocab[b[0]][0] for b in boxes]
        words = [w["word"] for _,_,w in text]
        matched = {}
        for block in SequenceMatcher(a=words, b=visual, autojunk=False).get_matching_blocks():
            if block.size < 3:
                continue
            for offset in range(block.size):
                matched[block.a+offset] = block.b+offset
        xmin = min(b[1] for b in boxes)
        xmax = max(b[1]+b[3] for b in boxes)
        kept = 0
        for ti, vi in matched.items():
            if matched.get(ti+1) != vi+1:
                continue
            line, i, w = text[ti]
            other, oi, ow = text[ti+1]
            if line["locus"] != other["locus"]:
                continue
            a,b = boxes[vi],boxes[vi+1]
            overlap = min(a[2]+a[4], b[2]+b[4]) - max(a[2],b[2])
            if b[1] <= a[1] or overlap <= 0:
                continue
            lookup[(line["locus"], i)] = dict(x_start=(a[1]-xmin)/max(1,xmax-xmin),
                                             box_x=a[1],box_y=a[2],box_index=vi,
                                             geometry_gap=b[1]-(a[1]+a[3]))
            kept += 1
        audit.append(dict(page=path.stem, text_tokens=len(words), visual_tokens=len(visual),
                          block_matched=len(matched), adjacent_pairs=kept))
    matched_rows = [dict(r, **lookup[(r["locus"],r["index"])]) for r in rows
                    if r["kind"] in ("ordinary","drawing") and (r["locus"],r["index"]) in lookup]
    return matched_rows, audit


def write_csv(path, rows):
    if not rows:
        return
    keys = sorted(set().union(*(r.keys() for r in rows)))
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lines = load_lines(ROOT/"data/ZL3b-n.txt")
    rows = observations(lines)
    ordinary = [r for r in rows if r["kind"] == "ordinary"]
    folios = assign_folds(ln["folio"] for ln in lines)
    stems = assign_folds(r["stem"] for r in ordinary)
    manifest = dict(seed=SEED, folios=folios, stems=stems,
                    sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in [ROOT/"data/ZL3b-n.txt", ROOT/"FRONTIER_PROTOCOL.md",Path(__file__).resolve()]},
                    coordinate_tree=json.loads((ROOT/"data/frontier/source_tree.json").read_text())["sha"])
    (OUT/"manifest.json").write_text(json.dumps(manifest, indent=2))
    geom, alignment = attach_coordinates(lines, rows)
    write_csv(OUT/"alignment.csv", alignment)
    predictions = []
    print('Corpus', len(lines), 'lines;',dict(Counter(r['kind'] for r in rows)), 'coordinate rows',len(geom), flush=True)
    for fold in range(5):
        train = [r for r in ordinary if folios[r["folio"]] != fold]
        test = [r for r in rows if folios[r["folio"]] == fold]
        base = Model(train, identity=True)
        full = Model(train, identity=True, context=True)
        scored = score(test, base.predict(test), full.predict(test), "folio_transfer", fold)
        predictions.extend(scored)
        rng = np.random.default_rng(SEED+fold)
        scrambled = [dict(r) for r in test if r["kind"] == "ordinary"]
        for page in sorted({r["page"] for r in scrambled}):
            inds = [i for i,r in enumerate(scrambled) if r["page"] == page]
            initials = [scrambled[i]["initial"] for i in inds]
            rng.shuffle(initials)
            for i,initial in zip(inds,initials):
                scrambled[i]["initial"] = initial
        predictions.extend(score(scrambled, base.predict(scrambled), full.predict(scrambled), "scrambled_context", fold))
        hidden = hidden_candidates([ln for ln in lines if folios[ln["folio"]] != fold],
                                   [ln for ln in lines if folios[ln["folio"]] == fold])
        for r in hidden:
            r["stem_seen"] = r["stem"] in {t["stem"] for t in train}
        predictions.extend(score(hidden,base.predict(hidden),full.predict(hidden),"hidden_transfer",fold))
        # Boundary-specific fit separates transfer failure from an in-domain effect.
        bt = [r for r in rows if r["kind"] != "uncertain" and folios[r["folio"]] != fold]
        be = [r for r in test if r["kind"] != "uncertain"]
        bm = Model(bt, identity=True, boundary=True)
        fm = Model(bt, identity=True, boundary=True, context=True)
        predictions.extend(score(be,bm.predict(be),fm.predict(be),"boundary_fitted",fold))
        gt = [r for r in geom if folios[r["folio"]] != fold]
        ge = [r for r in geom if folios[r["folio"]] == fold]
        gm0 = Model(gt, identity=True, context=True, boundary=True)
        gm1 = Model(gt, identity=True, context=True, boundary=True, geometry=True)
        predictions.extend(score(ge,gm0.predict(ge),gm1.predict(ge),"geometry",fold))
        print('Completed folio fold',fold, 'hidden',len(hidden),'geometry',len(ge),flush=True)
        for sfold in range(5):
            ct = [r for r in train if stems[r["stem"]] != sfold]
            ce = [r for r in test if r["kind"] == "ordinary" and stems[r["stem"]] == sfold]
            assert not {r["folio"] for r in ct} & {r["folio"] for r in ce}
            assert not {r["stem"] for r in ct} & {r["stem"] for r in ce}
            cm0 = Model(ct)
            cm1 = Model(ct, context=True)
            predictions.extend(score(ce,cm0.predict(ce),cm1.predict(ce),"crossed_stem_folio",fold))
        write_csv(OUT/"predictions.csv", predictions)
        print('Completed crossed folds for folio',fold,flush=True)
    results = {}
    for exp in sorted({r["experiment"] for r in predictions}):
        subset = [r for r in predictions if r["experiment"] == exp]
        results[exp] = {kind:summary([r for r in subset if r["kind"] == kind]) for kind in sorted({r["kind"] for r in subset})}
    results["corpus"] = dict(lines=len(lines), clean_tokens=sum(w["clean"] for ln in lines for w in ln["words"]),
                            total_tokens=sum(len(ln["words"]) for ln in lines),
                            counts=dict(Counter(r["kind"] for r in rows)), coordinate_rows=len(geom))
    (OUT/"summary.json").write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2),flush=True)


if __name__ == "__main__":
    main()
