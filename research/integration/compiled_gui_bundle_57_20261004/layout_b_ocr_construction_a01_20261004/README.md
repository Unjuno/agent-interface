# Layout-B OCR construction probe A01

Status: frozen exploratory construction probe over retained engineering screenshots; not a live/formal comparison and not an efficiency result.

Erratum: the recipe in the executed `run_probe.py` was not the exact preprocessing recipe used to select the OCR parameters on the development frame. Parameter selection included grayscale conversion and a 32-pixel white border; this runner omitted both. The saved task-5/6 OCR outputs remain raw observations for the runner's actual recipe, but they are not a valid held-out result for the development-selected recipe. The audit therefore classifies A01 as method-misaligned HOLD, with an observed lack of exact matches, rather than a valid evaluation of the selected method. A02 freezes the complete development recipe and uses untouched plain/persistent screenshots.

## H/T/D/C/U

- **H:** On the retained Chromium layout-B fixture at 1280×800, a narrowly cropped input interior followed by 8× enlargement and Tesseract English `--psm 7` can read the exact token after entry without matching that token on the preceding empty field frame. Coordinates and preprocessing were selected on task-4's entered-value frame `077.png` only; the preprocessing mismatch described above invalidates A01 as a held-out evaluation of that selected method.
- **T:** Apply the frozen recipe `crop 280x26+499+546`, resize to `800%`, then `tesseract ... stdout -l eng --psm 7` to every available screenshot for tasks 5 and 6 (held-out task identities) in the ephemeral arm. Also run it on task-4 empty source frame `068.png` as a negative sanity check. Compare OCR output after whitespace trimming against the independent expected token from each saved `submission_records` row. Keep each raw stdout, input PNG SHA-256, crop PNG SHA-256, and command.
- **D:** CONSTRUCTION PASS only if tasks 5 and 6 each have at least one exact OCR frame after input, their earliest source frames do not match, and no screenshot in either task window yields an exact match before the value is visibly entered. Otherwise FAIL/HOLD the proposed crop adapter. No frame from task 4 contributes to held-out pass status.
- **C:** Layout-B geometry may differ within a window; screenshot scaling, caret placement, color/subpixel rendering, or local Tesseract build may change OCR. The synthetic grounding probe and saved POST scorer do not establish a live C-arm result.
- **U:** This uses three tasks from one retained engineering run and one operating-system/toolchain; no layout perturbation, cold caller composition, target acquisition, or task-level causal result is measured.

## Frozen identities

- Source run: `research/live_control/results/integrated-efficiency-live-orchestration-probe-02/`.
- Source run disposition: `report.json` states 0 model calls, 14 synthetic grounding invocations, engineering orchestration only, excluded from formal comparison.
- Training image: `arms/ephemeral/runtime/077.png` (task 4 only).
- Held-out task identities: task 5 expected token `t991028-5`; task 6 expected token `t991028-6`, from their exact saved submission records in `arms/ephemeral/task-details.json`.
- Negative sanity image: task 4 empty source `arms/ephemeral/runtime/068.png`.
- Frozen geometry/preprocessing/OCR: `280x26+499+546`, `800%` resize, Tesseract `--psm 7 -l eng`, strip outer whitespace only; do not normalize OCR characters or accept fuzzy matches.

## Execution

The exact executed command and per-frame raw OCR/digests are retained in `RAW.json`; this directory also contains `AUDIT.json` for independent aggregate checks and the A01 deviation disposition. The adapter itself is not changed by this probe.
