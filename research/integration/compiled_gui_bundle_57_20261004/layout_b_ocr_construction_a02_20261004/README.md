# Layout-B OCR construction probe A02

Status: prospective held-out construction probe over two untouched arms of a retained engineering orchestration run. It is not a live/formal comparison, a complete C arm, or an efficiency result.

## H/T/D/C/U

- **H:** A Tesseract recipe selected on one layout-B development screenshot can exactly read the entered token in the same frozen layout across independent plain and persistent arm screenshots, while returning no exact token for the corresponding empty source frames.
- **T:** Train/confirm only on ephemeral task 4's entered-value frame (`077.png`, oracle `t991028-4`). Then apply the frozen recipe to every saved screenshot from tasks 4–6 in the plain and persistent arms. Determine each task interval from its source screenshot number up to (but excluding) the next task's source screenshot; task 6 extends through the final saved screenshot. Compare output after trimming outer whitespace only with the independent exact submission record. Preserve each raw output and input/crop digest.
- **D:** Construction PASS only if all six held-out task/arm cases each have at least one exact OCR match, the first source image in every case does not match, and each first positive is visually confirmed to show the entered exact value before the independent saved submission. Any missing or ambiguous case is FAIL/HOLD. No post-result threshold, crop, or preprocessing changes are allowed.
- **C:** The source run uses synthetic fixed grounding; all held-out screenshots come from one captured run and same Chromium fixture. The OCR locale, text rendering, task distribution, and layout geometry may be narrower than another host or real application.
- **U:** This does not measure target acquisition, caller cold cost, planner quality, GUI action reliability, independent live effect verification, user latency, or A/B/C/D efficiency. One training example and six held-out task-arm cases do not estimate a general OCR error rate.

## Frozen recipe and source

Development recipe confirmed on task 4: `magick INPUT -crop 280x26+499+546 +repage -alpha remove -colorspace Gray -resize 800% -bordercolor white -border 32 CROP`; then `tesseract CROP stdout -l eng --psm 7`. Exact output is required; do not normalize OCR characters or accept fuzzy matches. Task 4 in the ephemeral arm is development-only and excluded from held-out statistics.

Source run is `research/live_control/results/integrated-efficiency-live-orchestration-probe-02/`. Its report declares 0 model calls, 14 synthetic grounding invocations, and engineering orchestration only, excluded from formal comparison. The previous A01 exposure used the same held-out task identities in the ephemeral arm, so A02 does not use that arm for held-out evaluation. Plain and persistent task screenshots have not been inspected or OCR-processed before this freeze.

## Runtime boundary

The probe processes saved screenshots only. Current macOS host is Darwin ARM64. OrbStack reports no running containers; `docker image ls --digests` fails on a containerd content blob (`operation not supported`), so this probe will run natively and will not be described as a container result. It does not connect to the GUI or emit input.

## Execution and retained artifacts

Run `python3 research/integration/compiled_gui_bundle_57_20261004/layout_b_ocr_construction_a02_20261004/run_probe.py` after freezing this file. The script writes `RAW.json` with the development result and every held-out frame. Then run `python3 research/integration/compiled_gui_bundle_57_20261004/layout_b_ocr_construction_a02_20261004/audit_probe.py`; it writes `AUDIT.json`. The auditor replays every cropped OCR call from source PNGs and checks the recorded hashes, task grouping, exact-token oracle comparison, source-frame negatives, and protocol criteria.

Observed result: the development frame reads exactly and all 56 held-out frame/source/pixel/OCR/oracle checks reproduce. Source frames are empty OCR in all six cases. Exact held-out OCR succeeds only for plain task 4 at frame 065 and persistent task 4 at frame 083. Plain and persistent tasks 5 and 6 have no exact matches, due to initial `t`/`1` ambiguity and caret/parenthesis noise. The two positive frames were visually inspected and show the exact typed token. Disposition: **FAIL_FROZEN_LAYOUT_B_OCR_EXACTNESS** (four of six task-arm cases fail); no promotion to live or efficiency evidence.

The probe took 15.295751 s for these 56 images on the stated native macOS toolchain. This is scanner-workload time only. The independent audit does not attest the PNG's original host provenance or serve as a separate human visual reviewer.
