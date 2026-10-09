# Classical sources for synthetic-cipher engineering tests

Pinned Perseus Digital Library editions, not Voynich evidence:

- Caesar, De bello Gallico, T. Rice Holmes, Oxford/Clarendon, 1914.
  canonical-latinLit commit 128a05afa9cc7179ab18f8d05f78a9f1dd50e415.
- Homer, Iliad, David B. Monro and Thomas W. Allen, Oxford/Clarendon,
  1908–1920. canonical-greekLit commit 01b725d835e6e733062ffd79e0efdbae1ba06e5c.

Each XML has a .source.json sidecar with its acquisition URL.
Attribution: Perseus Digital Library / Trustees of Tufts University and the
contributors in the TEI headers. Both repositories supply CC BY-SA 4.0;
license texts are retained here. Derived text remains under that license.

The corpora module extracts TEI body text, excluding notes, headings,
bibliography and speaker labels. Latin uses existing accent folding.
Greek strips diacritics, folds final sigma and maps 24 retained letters
one-to-one into an ASCII storage alphabet. This is modern engineering
preprocessing, not historical transliteration or restoration of orthography.

Round-trip and focused study spans refer to the prepared stream. The original
frozen benchmark retains its raw-character span convention. Source and
prepared hashes accompany the evidence.

## Latin medical calibration (8 October follow-up)

`celsus_medical.txt` contains *De Medicina* books 1–8 from the Spencer edition;
`pliny_medical.txt` contains *Naturalis Historia* books 20–27 from the Mayhoff
edition. Each sidecar records the immutable upstream URL/commit, raw XML hash,
derived-text hash, book selection, extraction and attribution. The shared
`canonical-latinLit-LICENSE.md` applies (CC BY-SA 4.0); these derived texts retain
that license and attribute Perseus/Tufts and the named editors. Regenerate into
a new directory with `python -m voynich.acquisition.medical_corpora --output DIR`.
These are ancient medical/herbal proxies, not medieval recipe transcriptions.
