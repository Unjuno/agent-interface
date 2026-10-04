# Layout-B OCR fit diagnostic

Status: retained engineering diagnostic; excluded from the formal comparison.

## Provenance

The source is `research/live_control/results/integrated-efficiency-live-orchestration-probe-02/`, whose `report.json` explicitly says `model_calls=0`, `synthetic_grounding_invocations=14`, and `claim="engineering orchestration only; excluded from formal comparison"`. The task-4 record is layout B and records a fixed synthetic field point `[650, 558]` and submit point `[688, 634]`. Its saved scorer record says the expected and submitted token were both `t991028-4`, exactly once.

SHA-256 pins:

| File | SHA-256 |
|---|---|
| `report.json` | `0032980ac26052bd248e9cdca64fd8e18e7adaf13b5b2742fb58bd93fb709ca1` |
| `arms/ephemeral/task-details.json` | `4c1403549d562f11e39b986c984b2ab93b4ec3b554b01ef7c129d748cfeaac5d` |
| `arms/ephemeral/runtime/068.png` (task-4 source image) | `e1416a9e8e5c084dbc888af20f7d43c2475163fe01879ebd748bb4c4ac71ad2f` |
| `arms/ephemeral/runtime/077.png` (task-4 entered-value image) | `f07a6655e0f633db72a37450690282704cfa490aa2feb8f8e36c2524d4e8a185` |

## Erratum and corrected observation

An earlier attempt in this note incorrectly treated an empty Tesseract result on a crop written under `/tmp` as an OCR miss. Tesseract could not read those `/tmp` inputs, so that empty output was a path/tool-access failure and is invalid OCR evidence. The earlier claim that the layout-B crop returned empty has been withdrawn. The full-frame `--psm 11` result was produced from the retained repository screenshot and remains valid: it reads `1091028-4`, while the independent scorer records `t991028-4`.

The A01 construction probe applied crop `(499,546,280,26)`, 8× resize and Tesseract `--psm 7` to ephemeral-arm tasks 5 and 6. It produced no exact token match in either task window: task 5's best-looking outputs read `1991028-5` (missing `t`), and task 6's readout included a trailing caret mark or read `1991028-6`. Its task-4 blank-field negative returned empty text. However, the earlier dev-selection run that appeared to justify this geometry/scale/PSM also used grayscale conversion and a 32-pixel white border. A01 omitted both, so A01 is **HOLD for a development/execution recipe mismatch**, not a valid held-out evaluation of the method selected on task 4. See `layout_b_ocr_construction_a01_20261004/README.md`, `RAW.json`, and `AUDIT.json`; the audit reproduces the saved OCR stdout and source PNG hashes but records non-reproducible crop PNG byte hashes because the crop intermediates were not retained. A02 freezes the complete development recipe and uses untouched plain/persistent screenshots. Layout B remains unqualified for C, and the engineering probe's successful task-4 POST is not compiled-arm evidence.

## A02 held-out construction result

A02 first confirmed the development recipe on the ephemeral task-4 entered-value frame (`t991028-4`) and on its empty source frame (no text). It then froze that exact recipe and applied it to 56 screenshots across task-4/5/6 in the previously uninspected plain and persistent arms. Independent audit status is `PASS_SOURCE_CROP_PIXEL_AND_OCR_REPLAY`: zero source-image, regenerated crop-pixel, OCR-output, or scorer-oracle mismatches. All six task source frames produce no OCR output and no exact false positive. Exact positives appear only in task 4 (plain frame 065 and persistent frame 083); tasks 5 and 6 in both arms have zero exact-token frames. For task 5, OCR alternates between the correct initial `t` plus a trailing caret mark and a `1` in place of `t`; task 6 has the same initial-character ambiguity plus caret/parenthesis artifacts. Visual inspection of both positive frames confirms the exact token is visibly entered. The frozen decision is **FAIL_FROZEN_LAYOUT_B_OCR_EXACTNESS** because four of six held-out task-arm cases fail exact OCR.

The A02 script ran natively on Darwin ARM64, Python 3.14.5, ImageMagick 7.1.2-23 and Tesseract 5.5.2 because the current OrbStack image inventory fails on a containerd content blob. It took 15.30 s for 56 saved frames; this is only OCR construction-workload timing and says nothing about live control or efficiency. The source run is explicitly synthetic-grounding engineering data and excluded from formal comparison. A02 script, raw per-frame outputs/pixel hashes, and independent replay audit are retained in `layout_b_ocr_construction_a02_20261004/`.

Reproduction on the retained raw inputs from the repository root (diagnostic only):

```sh
mkdir -p work/layoutb-ocr-diagnostic
magick research/live_control/results/integrated-efficiency-live-orchestration-probe-02/arms/ephemeral/runtime/077.png -crop 280x26+499+546 +repage -resize 800% work/layoutb-ocr-diagnostic/task4.png
tesseract work/layoutb-ocr-diagnostic/task4.png stdout -l eng --psm 7
tesseract research/live_control/results/integrated-efficiency-live-orchestration-probe-02/arms/ephemeral/runtime/077.png stdout --psm 11
```
