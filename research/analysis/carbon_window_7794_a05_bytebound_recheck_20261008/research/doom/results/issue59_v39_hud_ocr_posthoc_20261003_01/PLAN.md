# Issue #59 — independent HUD OCR post-hoc probe

## H / T / D / C / U

- **H:** A generic OCR engine can recover health values from retained MAP01
  HUD frames without using the repository's WAD-specific digit matcher.
- **T:** Select every typed-observation row whose health value differs from
  the preceding typed row. Crop the fixed HUD box `(423, 591, 501, 629)` from
  its corresponding screenshot, scale 10x with nearest-neighbor, and run
  Tesseract with PSM 7/8/10/13 on grayscale, threshold-150, and inverted
  threshold-150 variants. Whitelist `0123456789%`; preserve the complete raw
  OCR strings. Compare normalized digits descriptively with the recorded
  typed values.
- **D:** `research/doom/results/map01-v39-coast-liveness-live-01/runtime/`
  from base commit `e5270c7bfe50911225afc6c3b5273021331b2bb1`. The retained
  `events.jsonl` SHA-256 is
  `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`;
  `sources.json` SHA-256 is
  `3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8`.
- **C:** Candidate is Tesseract 5.5.2 plus the fixed image preprocessing above.
  The existing typed value comes from the same retained run's WAD-specific
  `doom_hud_signal_v3.py` (SHA-256
  `9bd6b7462adfa6c07f1ab0a0820280768ccb9eff14aca32956a14538c0acb6d7`).
  This is agreement with an upstream extractor, not independent ground truth.
- **U:** At most, this probes whether a generic recognizer is a viable
  independent signal reader for a later prospective test. It does not establish
  useful-feedback onset, causal damage, control benefit, recovery efficacy, or
  any #59 live gate.

## Evidence status

This is deliberately **post-hoc exploratory**. The 73-to-72 frame pair was
already inspected, and the same OCR matrix was run once informally before this
package was frozen. The packaged run reproduces and retains that analysis; it is
not an independent replication. There is no blind human-labeled test set and
no preregistered acceptance threshold. Preserve all 14 selected frames and all
12 OCR configurations; do not select a winning configuration as if it were a
held-out result. No live game, model call, input, or allocation is authorized
or used.

## Reproduction

Run from this directory using Python with Pillow and Tesseract 5.5.2:

```sh
python3 experiment.py
python3 audit.py
python3 -m unittest -v
python3 -m py_compile experiment.py audit.py test_experiment.py
```

The experiment writes `RESULT.json`. The audit verifies the retained source,
selected frame hashes, RGB digests, complete configuration matrix, and
recomputed descriptive agreement counts; it does not certify independent
semantic labels.
