# Inputs to the robustness gate and mechanism benchmark

Sources, immutable upstream revisions where available, and SHA-256 hashes are
in `sources.json`. Downloaded 24 September 2026.

* `IT2a-n.txt`: Takeshi Takahashi's transcription as extracted from the
  Landini–Stolfi interlinear file, converted to IVTFF by René Zandbergen. This
  represents the older Takahashi reading, not a new transcription. The origin
  at https://www.voynich.nu/data/IT2a-n.txt returned HTTP 406 to the download
  client, so a commit-pinned copy from `oklo/voynich_gpt` was used. Its header is
  version 2a, 2 February 2023; the current origin has a later modification note.
  The report must not silently describe this mirror as the latest origin file.
* `naibbe_tables.csv`, `upstream_naibbe.py`, `upstream_naibbe_v2.py`,
  `upstream_README.md`, `upstream_LICENSE`: Michael A. Greshko's Naibbe project,
  https://github.com/greshko/naibbe-cipher, at commit
  `f2675ec5dd275268bc64dd48ea64fc0e0e9827a2`.
  Citation: Greshko, M. A. (2025), *The Naibbe cipher: a substitution cipher
  that encrypts Latin and Italian as Voynich Manuscript-like ciphertext*,
  Cryptologia, https://doi.org/10.1080/01611194.2025.2566408.
  The modified MIT license and attribution requirement are preserved locally.
  Upstream programs were inspected, not executed. Our encoder uses the tables
  with explicitly different sampling and ambiguity handling; it must not be
  represented as the published card-deck cipher.
* `voyn_101.txt`: Glen Claston's v101 transcription, downloaded from the pinned
  Rozanova/Temerev archive used in the previous stage. This is a legacy-byte
  alphabet, not UTF-8 EVA. It was inspected but NOT converted or analyzed in the
  direct n/l/r robustness check, to avoid unvalidated character mapping.
* `benchmark_tree.json`: discovery metadata from a public transcription archive;
  no text from it enters the experiments.

Existing Latin and Italian corpora are reused from `data/latin_alfonsi.txt` and
`data/italian_dante.txt`; their original download locations remain in
`code/fetch_data.py`. Normalization removes spaces and punctuation and maps
j→i, k→c, w→uu. Reversibility claims apply to that normalized letter stream,
not to recovery of capitalization, punctuation or original word boundaries.

No new Python libraries were needed for these experiments.
