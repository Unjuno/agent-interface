# A6 fixed quarter-frame ROI capture overhead — first outcome

Decision by the frozen auditor: `REJECT_ROI_CAPTURE_COST`.

A6 is a fresh one-factor successor to A4/#1061. It preserves the exact A4 Tk fixture, 20 Hz period, 500 ms raw ring, 300 ms warmup, 1500 ms measured interval, six counterbalanced matched pairs and all inherited overhead gates. The only scientific change is candidate XGetImage extent: full 320×240 -> fixed centered 160×120 ROI `[80,60,160,120]`.

## First outcome

Formal invocation1, reruns/replacements/tuning0. All six baseline arms complete the full interval with fixture_count94 and severe baseline stalls0. All six candidate arms terminate after exactly18 successful ROI captures at about900 ms because the same exception occurs in every arm: `TypeError('string argument without an encoding')`.

The source-localized compatible expression is `bytes(img.data)` in the frozen capture loop. The result therefore does not establish that quarter-frame ROI capture is too expensive. It establishes that this A6 python-xlib ROI payload path is not mechanically valid for the complete frozen interval, and the preregistered capture-count/exception/count-ratio gates reject it. The allocation is not rerun or relabelled.

Pre-exception measurements are diagnostic only: ROI raw frame76,800 bytes; ring max844,800 bytes=11 frames; capture p95 across pairs0.451–1.178 ms; measurement-process CPU fraction0.65%–1.21%; no candidate max fixture gap exceeds its paired baseline by more than2.633 ms. These favorable partial timings cannot count as a PASS because every candidate terminates early.

Frozen audit errors: pair0..5 `capture_count`, pair0..5 `capture_exception`, and `paired_count_ratio`; paired count-ratio p50=0.6010638298. Result SHA-256 `891106f22dbf55b5bf4ea31b872a5629a1a935bb61d2b88e189350683bde7e70`; audit SHA-256 `fca18f7670aac49f74ea2f0cbdbe43efe643dde0e4b21d4c42958d75bfceff72`.

## Integrity history

Source-first GitHub readback matched all five frozen scientific source blobs before formal. Postformal local source rehash remained exact. The initial publication of `FORMAL_RESULT.json` preserved semantic values but changed JSON formatting; publication was stopped and the GitHub file was restored to the exact first-outcome bytes, Git blob `c04fbce7c2685b35daa7dd8b8ccf22362f1369ee`, without rerunning or regenerating the formal allocation.

## Next discriminator

Do not rerun A6. A fresh successor may change only XImage payload normalization so byte-like and string-like python-xlib replies are losslessly converted to bytes, with unknown/non-Latin-1 payloads failing closed. ROI, cadence, XGetImage primitive, fixture, timing and scientific gates must remain unchanged. That successor can then answer the actual ROI-cost question.

## Scope

Linux/Xvfb/python-xlib/Tk only. Fixed ROI does not establish dynamic ROI discovery, XDamage semantics, privacy adequacy, model demand for history, task correctness, token savings or production capture cost.
