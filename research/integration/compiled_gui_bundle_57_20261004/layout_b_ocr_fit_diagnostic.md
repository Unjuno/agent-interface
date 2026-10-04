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

## Observation and OCR probe

Both PNGs are 1280×800. Inspection of the saved source frame and entered-value frame puts the layout-B input rectangle at approximately `(495, 541)–(803, 577)` in screenshot pixels, around the recorded point `(650, 558)`. The exact crop box was fed through local Tesseract after 4× resize and returned an empty string. Full-frame Tesseract `--psm 11` produced `1091028-4`, while the independent saved scorer has `t991028-4`; this is not an exact OCR match. The value is visibly present in the saved entered-value image and the exact independent POST record confirms the submission, but neither fact makes this OCR probe pass.

This exposes a concrete fit gap: a second fixed rectangle is insufficient as an exact-effect adapter. The current #7384 adapter rejects layout B; adding a guessed layout-B crop and marking `exact_token_visible=true` would be unsound. The next adapter should use the actual frozen layout-B observation path and demonstrate exact-token OCR on held raw frames (including a blank pre-entry frame), with the independent saved scorer still separate from its visual continuation predicate. Until then, layout B remains unqualified for C and task 4 must not be counted as compiled-arm evidence.

Reproduction on the retained raw inputs (diagnostic only):

```sh
magick arms/ephemeral/runtime/077.png -crop 308x36+495+541 +repage -resize 1232x144 /tmp/layoutb-077-crop.png
tesseract /tmp/layoutb-077-crop.png stdout --psm 7
tesseract arms/ephemeral/runtime/077.png stdout --psm 11
```

