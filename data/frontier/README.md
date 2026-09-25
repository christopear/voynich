# Coordinate input provenance

Downloaded 24 September 2026 from the public reproducibility archive:
https://github.com/lrozanova/voynich-units

Pinned Git tree: `956a7c4fc39981f4d116fa3f4edfccce6d065571`.

The initial protocol called this a commit; GitHub's recursive-tree endpoint
actually returned a tree object. It still pins the file contents, and the
supplement manifest additionally hashes every downloaded coordinate file.

`boxes/*.js` are the archive's 223 JSON-format token coordinate files from
`data/voynich-units/morphometry_voynichese/voynichese_boxes/`. Its documentation
attributes the underlying coordinate data to Voynichese.com. Each file contains
a vocabulary and a sequence of `[vocabulary_index, x, y, width, height]` entries.
Coordinate units belong to that dataset's image grid, not original scan pixels.

`source_tree.json` records the upstream tree. `upstream_README.md` and
`upstream_LICENSE` preserve the archive's documentation and code license.
Third-party data retain their original provenance and rights; the archive's code
license is not a new license granted by us for the historical images or data.
No Yale manuscript images were downloaded or redistributed in this experiment.

`coordinate_methods_reference.py` is an unexecuted copy of the upstream
`analysis/reproduce_headlines.py`, retained to document the format and existing
alignment approach. Our analysis is in `code/06_boundary_frontier.py` and uses
stricter exact matching. `f3r_sample.js` duplicates the first inspected box file.

Re-fetch missing coordinate files using `uv run python code/fetch_frontier_coordinates.py`.
