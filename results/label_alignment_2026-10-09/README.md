# Recurring-label alignment packet

Preparation only; no semantic fitting. Exact coordinate candidates are in
`packet.json` and [the review table](report.html). Four label types cross the
original folio split: otaly, okeoly, okydy, okaram. The scope required five;
therefore its semantic test gate fails before fitting. Do not lower it post hoc.

All 22 recurring types are included for manual alignment. Exact matches to the
cached Voynichese coordinate vocabulary are candidates only, not confirmation
that a box belongs to the same ZL locus or illustrated figure. Missing matches
are retained; no fuzzy equivalences invented. Coordinates are not Yale pixels.
No source drawings or lexical meanings have been assigned automatically.

Producer: `python -m voynich.laboratory.label_alignment_packet --output results/<new-dir>`.
Source and coordinate hashes are in the packet; coordinate provenance is in
`data/frontier/README.md`. The original glyph/image alignment remains to be
completed before a new semantic protocol can be considered.
