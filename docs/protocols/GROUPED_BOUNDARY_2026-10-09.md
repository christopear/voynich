# Bounded prefix codes and uncertain boundaries — 9 October 2026

Prospective search protocol; exploratory structural inspection preceded it.
Ledger target: row 12, grouped/verbose units. This is a new representation, not
another budget comparison for length-preserving substitution. No historical
attestation is claimed for this particular combination of manual operations.

## Family and scope

One fixed table. A declared set of at most THREE glyphs introduces two-glyph
codes; all other initial glyphs are single-glyph codes. Codes emit one lowercase
letter, or (in encoded-space mode) a space. At most two codes emit the same unit.
No nulls, transposition, tables changing by position, or code splitting across
line boundaries / unclean omitted slots. These are restrictive model assumptions.

Spacing arms: preserve every retained written word boundary; or ignore written
spaces and infer plaintext boundaries via explicit space-emitting codes. This
second arm does NOT permit arbitrary inserted spaces or an unrestricted parser.
Compound EVA; unclean words break both parsing and language context. Drawings
also break spans. Every retained glyph must be consumed exactly; no fallback
for truncated prefix codes. Group expansion must be 1.35–2.00 glyphs per code.
This is a design range, not the entropy screen's alleged universal minimum.

Enumerate all prefix subsets of size 1–3, plus the all-prefix fixed-width-two
policy. Reject policies violating complete parsing, expansion or the capacity
of 26/27 units × two homophones. Rank remaining policies by sorted unigram
frequency fit to the training model (two equally likely variants per unit),
then key size and lexical policy order. Retain at most FOUR. Screening effort
and all counts are recorded; it is data-dependent but receives no truth.
Each retained policy gets 4,096 beam proposals (width 8), including initialization.
No outcome-dependent budget extension. Select minimum total language + uniform
homophone-choice + explicit codebook + prefix-policy description cost per input
glyph. Reset language context at line/unclean/drawing boundaries.
This is a Viterbi/description-cost heuristic, not marginal model evidence.

## Calibration first

Celsus training vs Pliny passages, and Dante training vs disjoint Dante passages
(same author limitation). Training starts at 30%, up to 12,000 characters and at most 20% of the source;
passages at 70%, length 350; seeds 7/19 change encoding and search, not passage.
Both spacing arms. Prefix-free synthetic codes over 16 glyphs, three long-code
prefixes, two homophones, independently generated keys. Include known-key
round-trip, oracle parse representability, truth policy survival in the shortlist,
nonspace edit recovery and space-boundary accuracy after selection. Do not
supply key, prefix set or plaintext to screening/search. Report ciphertext
entropy/expansion and distribution mismatch; fixtures are not faithful replicas
of all Voynich properties. A capability gate requires >=90% nonspace recovery
in both seeds of each language/spacing arm. Failed calibration means actual
Voynich results are exploratory diagnostics and cannot reject the cipher family.

## Immediate manuscript trial

Use ZL3b Currier B herbal f26r; freeze selected key AND parser for f31r/f39v.
These pages have been examined before; no untouched-holdout claim. Seeds 7/19,
Celsus selection model, independent Pliny model only after selection.
Controls: original, global whole-word shuffle, symbol shuffle, and TWO word
permutations stratified by paragraph-first-line / paragraph-last-line status
and within-line first/last/interior word role. Preserve unclean slots. All arms
get identical policy enumeration and per-policy search budgets; totals may
vary with structural feasibility. Report this, not equal-total-budget claims.
No-control-survivor cases count as structural differences, not language wins.

Transfer never extends the key; unknown codes split language contexts; invalid
spans are reported, not silently reparsed. Report glyph coverage, valid span
coverage, full-span score and covered-run scores separately. Lower partial scores
with different coverage do not establish transfer improvement.
Compare selection scores, independent model scores, and mapping agreement across
seeds for the same policy. A promising follow-up needs calibrated recovery,
original beating every available matched control under independent language
scores, >=90% transfer glyph coverage, stable mappings and coherent readings.
These are prioritisation criteria, not calibrated p-values. Any result failing
them remains 'search found no fit / insufficient solver calibration'.

## Prior exposure and bookkeeping

Before this protocol, a scratch parse on f26r (20 compound glyph types, 340 retained
glyphs under the OLD gap-closing loader) found three expansion-qualified policies
with <=54 codes and none <=27. This motivated the capacity-two pilot; the new
loader preserves uncertainty gaps, so the count may change. No key search was
run or outputs inspected. Estimator sensitivity was also observed before this
protocol. Older reproduction jobs are not duplicated while Claude is running them.

Register each key search in PostgreSQL; retain top three/reservoir three and all
selected recipes. Save structural non-survivors, source hashes, policies, budgets,
full selected outputs, transfer masks, and an executive report. Commit this
protocol and implementation before running. Unit tests may use tiny fixtures.
Stop at this bounded round, update the ledger, and return for review.
