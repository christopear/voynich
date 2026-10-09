# Grouped codes and boundaries: a bounded negative result

**No new Voynich partial decryption.** The specified prefix-code family could
not reach the key-search stage on original f26r. Separately, its unigram parser
shortlist failed every synthetic calibration case. These findings narrow this
implementation's usefulness; they do not reject grouped or variable-length
ciphers generally.

[Open the operating report](report.html).

## What changed from the previous studies

Previous manuscript searches largely mapped one compound glyph to one letter.
This study tests one- and two-glyph codes, one fixed table, at most two codes per
plaintext unit, and two boundary assumptions: preserve written word spaces, or
ignore written spaces and decode plaintext spaces from explicit codes. Up to
three glyphs can introduce long codes; fixed-width two is also checked. Codes
cannot cross line endings, drawing breaks, or omitted unclean slots. Those are
substantive, restrictive assumptions, not established manuscript facts.

The intended expansion range is 1.35–2.00 glyphs per code. It is a declared
pilot range, not a minimum proved by the entropy screen. The new loader keeps
uncertainty gaps rather than closing them, giving 373 retained compound glyphs
in 30 spans on f26r. Earlier gap-closing page results are not directly comparable.

## Actual manuscript result

All 1,351 allowed prefix policies were screened in each spacing arm:

| Input | Preserved-space survivors | Encoded-space survivors |
|---|---:|---:|
| Original f26r | **0** | **0** |
| Whole-word shuffle | 0 | 1 |
| Symbol shuffle | 0 | 0 |
| Paragraph/line-role word shuffle 1 | 0 | 3 |
| Paragraph/line-role word shuffle 2 | 0 | 2 |

Counts repeat across optimizer seeds because structural screening is deterministic.
No original-page key was selected, so **no original-key transfer to f31r/f39v
was possible**. The exported control transfers do not substitute for that test.
No language-score win, stable reading, or significance claim follows from these
survivor counts. Each admitted policy got 4,096 proposals; total budgets therefore
differ with structural feasibility.

A **post-hoc diagnostic**, with no new key search or threshold changes, finds the
largest fully parsable expansion in this grid was 1.166 with written spaces and
1.323 with encoded spaces. The latter lies fairly close to the pilot's 1.35
cutoff. This reinforces the narrow scope: different expansion ranges, longer
codes, more prefix types, or different treatment of boundaries could admit models.
See [posthoc_structural.json](posthoc_structural.json).

## What the synthetic test actually demonstrated

Eight cases: Latin/Italian × two spacing assumptions × two independent key/search
seeds. The two seeds share a passage within each language. Latin uses Celsus to
train and Pliny as the target; Italian uses disjoint Dante passages, with the
same-author limitation. Synthetic glyph alphabet size is 16 versus 20 on f26r;
these are not complete replicas of Voynich's entropy, layout and page specificity.

| Language / spacing | Seed 7 nonspace recovery | Seed 19 |
|---|---:|---:|
| Latin / preserve | 13.9% | 9.3% |
| Latin / encoded | 14.2% | 16.6% |
| Italian / preserve | 16.1% | 5.7% |
| Italian / encoded | 25.4% | 12.5% |

**0/8 reached the 90% capability gate.** Known-key decoding was exact, including
64 spans independently decoded by the reference cipher's trie decoder.

The central failure is more specific than "beam search is weak": **the true
parsing policy survived the structural screen but was discarded by the unigram
shortlist in all eight cases**. It ranked last in seven cases and 26th of 28 in
the other; only four were searched. The full true-key score was better than the
selected result in all eight cases. This demonstrates a defective pruning
heuristic, not inability of the language scorer to prefer the known plaintext.
It does not establish that the present key search would recover the true key if
the true parser were retained. More budget on the shortlisted keys cannot repair
a parser that has already been removed.

## Research decision

Do not promote this shortlist rule or infer cipher-family rejection from these
searches. Do not respond by simply increasing the beam budget. Before another
blind grouped-code search, parser retention must be calibrated, and assumptions
about code boundaries at drawings/uncertain gaps must be justified or explicitly
varied. The broader grouped/variable-length family remains open.

The next scientific priority remains the constitution's unit-size versus
page-association study: test whether glyph groups, syllables, word codes or mixed
units can account jointly for page association and vocabulary shape under stated
spacing/layout assumptions. That can constrain a representation before another
large key search. Any subsequent solver improvement must return promptly to
actual manuscript trials, with uncertainty-preserving controls.

## Screen corrections and restored research

The new [entropy sensitivity report](../capacity_sensitivity_2026-10-09/README.md)
retains a substantial reference gap but withdraws universal language/family
exclusions. State independence must be stated; observable layout does not prove
it. Miller–Madow/block-size checks are sensitivities, and expansion is heuristic.
The 7–10× reference-spread description does not hold for the full five-source panel.

Claude's `10bce4c` records completed reproduction of restored stages 19–25,
including the moved-citation-string exception. Its two status commits were
merged; these historical runs were not duplicated in this continuation.

## Execution and review

Protocol and implementation committed **before search** at `0675c3b`; clean
execution source recorded. 28 case specifications underwent screening;
**44 registered searches, 180,224 evaluations, zero evaluator exceptions**.
All 44 database records and execution bindings verified; all **132 retained
candidates replayed exactly**; all 104 execution source hashes verified.
Post-hoc structural envelope and report generation did not change selected keys.

**199 tests passed**, including PostgreSQL integration, after restoring the
research modules and implementing the search. Package build passed. Reporting
and verification helpers were added afterward and checked separately.

- [Frozen protocol](../../docs/protocols/GROUPED_BOUNDARY_2026-10-09.md)
- [Evidence and all selected control outputs](evidence.json)
- [Comparisons](comparisons.json)
- [Run specifications](specifications.json)
- [Environment](environment.json), [plan](plan.json), [source page slots](pages.json)
- [Verification](verification.json)

Reproduce into a **new** directory (requires the local research database):

```
uv run --env-file .env --locked python -m voynich.laboratory.grouped_boundary --output results/runs/new-grouped-study
```

Generate the report from committed evidence:

```
uv run --locked python -m voynich.laboratory.grouped_report --input results/grouped_boundary_2026-10-09/evidence.json --output results/grouped_boundary_2026-10-09
```
