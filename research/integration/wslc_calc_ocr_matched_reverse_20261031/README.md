# WSLc Calc: reverse-order OCR invalidation comparison

This preregistered single-pair follow-up reverses the order of `wslc_calc_ocr_matched_invalidation_20261031`: fresh runs first (e12), then compiled with an intentionally stale reference (e13). It uses the same 15 frozen runner/fixture inputs, source snapshot, pinned image, known values and fixed-crop Tesseract cue. The previous and current model call IDs are disjoint. Both runs independently saved 329 and 517 and recorded neutral input releases. The compiled method returned `SAFE_YIELD` on the stale reference, did not replay entry, and performed a new guarded Save after OCR.

| Block / route | Host launcher | Task interval | Model calls | Input tokens (cached subset) | Output tokens |
|---|---:|---:|---:|---:|---:|
| Prior, compiled first | 13.078 s | 7.952 s | 1 | 12,197 (0) | 78 |
| Prior, fresh second | 13.782 s | 11.408 s | 2 | 25,779 (20,352) | 156 |
| Reverse, fresh first | 12.672 s | 9.528 s | 2 | 25,763 (12,160) | 124 |
| Reverse, compiled second | 10.422 s | 8.083 s | 1 | 12,197 (0) | 78 |

The launcher interval covers process start through host and container exit; the task interval begins after app startup and ends after independent scoring. Initial source/input preparation, stale-reference creation, image build/pull and postrun audit are excluded. There was no separate schema preflight. Input tokens include cached tokens, and billing is unknown.

These are two fixed-order observations using the same synthetic fixture and seed, not independent task populations. Cache, provider/load and method behavior remain different; the stale reference affects the compiled route only. Fixed geometry and known expected values limit perception claims. The results do not establish a general speed or reliability improvement, full end-to-end cost, second-domain completion, or MAP01 completion. Issue 57 remains open.

Run `python audit.py` with Pillow and the sibling prior archive present. The auditor verifies the packet manifest and frozen inputs, reconstitutes OCR crops and parses transcripts, independently parses saved FODS, checks guards/releases, model usage, cleanup and prior input/call-ID linkage. The private model session protocol journals are hash-indexed rather than published; source/image/provider bytes are not fully reproduced. Legacy OCR metadata reports psm 11 while the actual recorded runner calls use psm 7; the latter is a call trace, not an OS trace.
