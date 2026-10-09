# Reference-profile sensitivity, 9 October 2026

The Celsus–compound-EVA gap survives both estimators and increases with block
size. For orders 3/4, conservative minimum-reference minus maximum-cipher gaps:

| Block size | Plug-in | Miller–Madow |
|---|---|---|
| 5,000 | 1.416 / 0.935 | 1.480 / 1.008 |
| 20,000 | 1.865 / 1.756 | 1.892 / 1.833 |
| 40,000 | 2.090 / 2.213 | 2.106 / 2.272 |
| 80,000 | 2.189 / 2.388 | 2.197 / 2.424 |

These are priority-setting reference-profile gaps, not universal language bounds
or calibrated rejection rates. Fixed decoders obey H(P|S)<=H(C|S). The comparison
without a state allowance needs a fixed table or independence of plaintext
windows from state. Observable layout does not establish independence. A more
general bound is H(P)<=H(C)+I(P;S). Hidden independent random state obeys the same
independence argument; dependent state/additional context requires a new model.

The reported reference spread is the range of available reference mean entropies,
not a standard deviation. At 20,000 units the order-3/4 ranges are 0.851/0.934 bits
and include five sources: the Celsus gaps are about 2.2/1.9 times these ranges,
**not 7–10 times the spread across all five references**. At 40,000 and 80,000,
Italian and German drop out because they are too short, leaving a narrower
Latin-only panel. Ratios from those panels must not be described as applying to
all five sources. Miller–Madow is a sensitivity correction, especially limited
for sparse, overlapping windows; increasing gaps are robustness evidence, not a
guaranteed bias bound. The expansion calculation remains heuristic.

Reproduce into a new path:

```
uv run --locked python -m voynich.evaluation.capacity --sensitivity --output results/runs/new-capacity.json
```

No original screen JSON was overwritten. Input corpus paths and preparation are
in `voynich.evaluation.capacity`; the grouped-study environment records their
code and data hashes. Full sweep: [screen.json](screen.json).
