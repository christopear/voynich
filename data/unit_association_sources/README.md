# Sources for the unit/page-association study

Acquired 9 October 2026. Raw content is retained for offline reproduction.

- **Celsus, De Medicina**, books 1–8, W. G. Spencer edition (1935–1938).
- **Pliny, Naturalis Historia**, books 20–27 from the full Mayhoff edition
  (1906). Both TEI XML files are from PerseusDL/canonical-latinLit commit
  `128a05afa9cc7179ab18f8d05f78a9f1dd50e415`, compressed losslessly with gzip.
  Exact upstream URLs, raw SHA-256, edition attribution and licence are in the
  corresponding `.source.json`. CC BY-SA 4.0; licence copy at
  `../laboratory_sources/canonical-latinLit-LICENSE.md`. Original metadata's
  `text_sha256` describes the earlier whole-book medical corpus, not this
  study's chapter extraction. The new run manifest hashes prepared chapters.
- **Anonymous, Il libro della cucina del sec. XIV**, edited by Francesco
  Zambrini, Bologna, 1863. [Project Gutenberg 33954](https://www.gutenberg.org/files/33954/33954-h/33954-h.htm),
  digitized by Carla, Carlo Traverso, Barbara Magni and the Online Distributed
  Proofreading Team from Internet Archive images. Retained HTML includes the
  Gutenberg notice. This is a later edition of a medieval culinary text,
  not a diplomatic medical manuscript or a fifteenth-century language guarantee.

`python -m voynich.acquisition.unit_sources` inventories extraction. This skips
editorial headings, notes, the recipe introduction and printed page markers.
Prepared chapter groups and hashes are exported by experiment 27. Modern editorial
choices and source genres remain limitations. Existing Alfonsi and Dante local
files are literary contrasts and receive file hashes in that manifest.
