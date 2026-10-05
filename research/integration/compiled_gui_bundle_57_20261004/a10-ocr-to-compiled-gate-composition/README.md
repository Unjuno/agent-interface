# A10 — retained OCR through the compiled exact-value gate

## Result

`PASS_OCR_TO_EXACT_VALUE_GATE_COMPOSITION_SCOPED`. The source-linked A09 OCR strings were fed to the pinned A07 v2 adapter and compiled core across all six retained layout-B frames, using test-double actions and effects. Submit dispatch exactly matched OCR equality in all 18 paths:

| Observer text source | Exact values | Mock Submit dispatches | Task successes |
|---|---:|---:|---:|
| Frozen crop, local Tesseract | 4/6 | 4/6 | 0 |
| Padded crop, local Tesseract | 6/6 | 6/6 | 0 |
| Original archived OCR output | 3/6 | 3/6 | 0 |

Every mock action returned a unique ID and a verified empty key/button release. All paths ended `SAFE_YIELD`: a mismatched entry stopped before Submit, and each mock Submit stopped at `effect_unavailable` because no application result was observed. Thus the test proves the OCR-to-predicate-to-graph dispatch boundary only; it does not credit a task completion or an actual Submit.

## Provenance and checks

The experiment plan was frozen before execution in `PLAN.md`. Inputs are the six A09 rows (`RAW.json` SHA-256 `f00088019210ec3d8e4192fd4f4e34816cd689a22d67beb6388d71950ee660b6`), A07 adapter-v2 SHA-256 `f1f3f6b2a1f0487a9c6f65b51936fafc8b6101390b1e4070f8e31f741a28b6ef`, and compiled-core SHA-256 `d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014`.

The independent audit uses explicit checks rather than Python `assert`, validates image/crop/OCR provenance, and verifies the mock-action gate and stop outcomes. It passes under normal Python and `python -O`; a corrupted record that removes a required Submit dispatch is rejected in both modes. The retained raw is `RAW.json` (SHA-256 `8aae2133bcde0512ad51975ee11d62c13bff3d84198a98ee56a3045b882a2f9d`); `AUDIT.json` contains the scoped result.

## Limits

No new screenshot, live GUI, input, target acquisition, model/provider, container, or formal allocation ran. The OCR strings are from retained A05 frames; the original host's Tesseract environment remains unknown. The graph's target/admission/effect callbacks are test doubles. There is no evidence of successful application submission, end-to-end savings, or general reliability. The consumed A05 C result remains 9/12 and is unchanged.

The first harness attempt is retained separately in `RAW_ATTEMPT_01_STALE_OBSERVATION.json`; its synthetic capture clock was deliberately 1 ms stale, so the core refused all 18 paths before any Submit dispatch. `RUN_LOG.md` records that construction failure and correction.
