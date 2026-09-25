# voynich-units — reproduction code and data

> **A Glyph Is Not a Letter, a Token Is Not a Word, a Space Is Not a Space:
> What the Units of Voynichese Are Not**
>
> Liudmila Rozanova (IIASA) · Alexander Temerev (University of Geneva)

Self-contained reproduction package for the paper: every figure-generating
script, the supporting analysis drivers cited in the text, and the data they
read. This is the public mirror of the ancillary files bundled with the arXiv
submission. Code is released under the MIT licence; third-party data keep the
terms of their original sources, cited in the paper.

## Python environment

```sh
python3 -m pip install -r requirements.txt
```

NumPy, Matplotlib, and pandas are enough to regenerate every figure. `pypinyin`
is used only by the syllabic-control script; OpenCV (`opencv-python`) is needed
only to *re-run the raw ink measurement* — the archived measurements are already
provided, so it is not required to rebuild the figures.

## Figures and how to reproduce them

Each script writes its PNG into `figures/` (create it first). Run from this
directory.

| Fig | File | Script | Command |
|-----|------|--------|---------|
| 1 | `F0_scale_transition_publication.png` | `reproduce_scale_transition.py` | `python3 analysis/reproduce_scale_transition.py voynich_decipherment_repro_bundle --public-data-root data/voynich-units` |
| 2 | `F1_boundary_coordinate_publication.png` | `reproduce_headlines.py` | `python3 analysis/reproduce_headlines.py data/voynich-units --v101 data/v101/voyn_101.txt --output figures` |
| 3 | `F4_dialect_linestart.png` | `reproduce_dialect_linestart.py` | `python3 analysis/reproduce_dialect_linestart.py data/voynich-units --figure-output figures` |
| 4 | `F3_unit_scale_publication.png` | `reproduce_unit_scale.py` | `python3 analysis/reproduce_unit_scale.py voynich_decipherment_repro_bundle --output figures` |
| 5 | `F4_cipher_calibration_publication.png` | `reproduce_cipher_calibration.py` | `python3 analysis/reproduce_cipher_calibration.py voynich_decipherment_repro_bundle` |
| 6 | `F6_direct_pixel_publication.png` | `reproduce_direct_pixel.py` | `python3 analysis/reproduce_direct_pixel.py --data data/direct_pixel --output figures` |
| 7 | `F7_robustness_publication.png` | `reproduce_direct_pixel.py` | (same command as Fig 6) |

- **Fig 1** — word-like inventory vs. token-order share.
- **Fig 2** — boundary association by transcription (A) plus the independent
  image-coordinate validation (B–D).
- **Fig 3** — Currier A/B boundary profiles (A) and line-start decomposition (B).
- **Fig 4** — recurrent multi-symbol unit scale (BPE).
- **Fig 5** — learned-unit substitution attack (calibration and application).
- **Fig 6** — blind direct-pixel validation (boxplots + per-folio).
- **Fig 7** — robustness of the direct-pixel check (threshold, geometry QC, estimators).

The bootstrap/shuffle drivers accept quick-test flags (e.g.
`--bootstrap 100`, `--shuffles 10`, `--partitions 10`, `--jsd-null 10`) that
change only the interval widths, not the point estimates. Every driver fixes
its seeds and takes its input roots as explicit arguments.

## Supporting analysis drivers

Beyond the figures, `analysis/` also contains the checks cited in the text:
`reproduce_space_sensitivity.py` (space-erasure / hidden-boundary),
`reproduce_edge_order.py` (edge-glyph order), `reproduce_unit_inventory.py`
(learned units against published inventories), `reproduce_naibbe_control.py`
and `reproduce_selfcitation_control.py` (the two further controls).

## Direct-pixel measurement code and data

- `data/direct_pixel/` — the archived blind-audit results:
  `results_unblinded.csv` (per-boundary gaps, labels, geometry),
  `threshold_sensitivity.csv`, `estimator_robustness.csv`.
  `reproduce_direct_pixel.py` builds Figs 6–7 directly from these.
- `analysis/direct_pixel/` — the measurement pipeline itself:
  `measure_direct_pixels.py` (blind ink-gap measurement from page images) and
  `analyze_direct_morphometry.py` (label reveal + statistics). Re-running these
  requires the frozen manifest and the Beinecke page scans (not redistributed;
  see below) plus OpenCV.

## Data provenance

Included: the ZL3b and v101 transcriptions, the per-token coordinate boxes, the
classical/Project-Gutenberg control corpora and language-model corpora, the
cipher-calibration and BPE result bundles, the Chinese pinyin controls for the
syllabic test, and the archived direct-pixel measurements.

**Not redistributed:** the Beinecke/Yale page scans used by the raw direct-pixel
measurement (Yale IIIF licensing). The archived per-boundary measurements are
provided instead, so Figs 6–7 are fully reproducible without the scans.

## Folder map

```
analysis/                           figure + supporting scripts
analysis/direct_pixel/              raw ink-measurement pipeline
data/                               transcriptions, controls, coordinate boxes,
                                    v101, direct-pixel measurements
voynich_decipherment_repro_bundle/  BPE / cipher / syllabic result bundles + corpora
requirements.txt                    Python dependencies
```
