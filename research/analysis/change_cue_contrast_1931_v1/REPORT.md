# #4436 — source-preserving contrast-guaranteed change cues

## Disposition

**PASS_SOURCE_PRESERVING_CONTRAST_CUE_SCOPED** on separately frozen allocation `change-cue-contrast-4436-v2`.

The consumed v1 allocation is retained separately as `STOP_FORMAL_ENVIRONMENT_API_MISMATCH`: Python 3.13.5 rejected the frozen `gzip.open(..., mtime=0)` call before any scientific row was produced. V2 changed only that gzip writer API argument; H/T/D/C/U, corpus, transforms, scorer and gates were unchanged.

## Result

- source cases: **19,520**
- cue rows: **78,080**
- changed-ROI byte damage: **0**
- inverse coordinate-map failures: **0**
- fixed-green exact 1:1 contrast rows: **20**
- fixed-green rows below 3:1: **11,280**
- minimum fixed-green contrast: **1.000000:1**
- minimum adaptive B/W contrast: **4.585027872938:1**
- minimum dual B/W max-stroke contrast: **4.585027872938:1**
- analytic lower bound: `sqrt(21)` = **4.582575694956:1**
- adaptive bound violations: **0**
- dual bound violations: **0**
- unpadded clipped cue rows: **46,848**
- padded dual completeness failures: **0**

Fixed green therefore has a direct counterexample: a green source background makes the green outline indistinguishable by this luminance-contrast metric. Choosing the better of black/white satisfies the declared contrast floor across the complete frozen color/geometry corpus. Padding restores complete two-stroke geometry at source edges/corners while retaining an exact inverse source-coordinate map.

## Audit

Independent `audit.py` does not import the candidate runner. It re-read all **78,080** retained rows, independently recomputed color contrast and aggregate gates, and reported **PASS_AUDIT** with zero errors. All **11** deliberate result/evidence mutations were rejected.

## Publication evidence

The actual formal `ROWS.csv.gz` is 4,756,475 bytes with SHA-256 `193d4ceb87c507fafea9e7525658b515f2dcc3f1fcd5dd1a889151b0baecbdd0`; its decompressed CSV is 22,981,634 bytes, 78,080 rows, SHA-256 `e0a249a57122076933a0cebf3378211c10466c451c870e17519c738a25aa5100`. Because the available GitHub MCP contents path is UTF-8-text oriented, the reviewable branch publishes a compact **lossless measurement-column corpus** as base64(xz(csv)), plus ordered roots for the three deterministically recomputable per-row hash columns, exact original digests, and 32 raw witness rows. `RAW_MANIFEST.json` states this limitation explicitly; it does not claim byte-for-byte GitHub retention of the original gzip.

## Scope / what this does not establish

This result establishes only a **presentation integrity prerequisite**. WCAG-style luminance contrast is human-oriented and is not a measurement of Astra/VLM attention. No model/provider, GUI, task action, token, latency, or human-tempo experiment ran. Strong cues may still distract a VLM or cause attention tunneling. The actual #1931 question therefore remains open and requires a same-model RAW-vs-cued experiment.

## Next empirical residual

Use the source-preserving adaptive/dual cue as one fixed candidate, hold raw screenshots/model/task constant, and measure subtle-change localization/detection plus an uncued-change negative control. Do not infer that this scoped contrast PASS predicts the model result.
