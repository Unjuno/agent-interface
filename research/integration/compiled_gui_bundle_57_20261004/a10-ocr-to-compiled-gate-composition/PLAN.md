# A10 — OCR output through the compiled exact-value gate

## H/T/D/C/U

- **H:** Feeding a source-linked OCR string into A07's exact-value observer predicate causes the compiled graph to dispatch `activate_submit` if and only if that string exactly equals the task token. A wrong or incomplete string must stop after entry. A submitted action must not become task success without independent post-submit evidence.
- **T:** For tasks 4–6 in both A05 blocks, consume A09's pinned `RAW.json` (`f00088019210ec3d8e4192fd4f4e34816cd689a22d67beb6388d71950ee660b6`). Run the frozen-crop output, padded-crop output, and original archived OCR output through the pinned A07 v2 adapter and compiled core. Use test-double action/admission/effect callbacks only. Independently audit all 18 paths.
- **D:** Scoped pass requires `activate_submit` iff the selected OCR text exactly matches the task value, no submit on mismatches, unique receipts with verified empty input release for each mock action, and zero `TASK_SUCCEEDED` outcomes because post-submit evidence is deliberately unavailable. Any mismatch fails the composition gate.
- **C:** The only visual inputs are retained post-run frames and OCR strings; action dispatch and release are test doubles. This tests the connection from OCR result to the compiled predicate, not live input, application behavior, or observer provenance at runtime.
- **U:** No live GUI, fresh capture, provider/model, target acquisition, input, submit effect, authority, privacy, latency, or efficiency was measured. The OCR values come from local Tesseract 5.5.2 and the original A05 host's OCR environment remains unknown. A10 cannot amend A05's 9/12 outcome or authorize another formal allocation.

## Frozen inputs

- A09 raw SHA-256: `f00088019210ec3d8e4192fd4f4e34816cd689a22d67beb6388d71950ee660b6`.
- A07 adapter-v2 SHA-256: `f1f3f6b2a1f0487a9c6f65b51936fafc8b6101390b1e4070f8e31f741a28b6ef`.
- Compiled-core SHA-256: `d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014`.
- Frozen/candidate crop labels, source frame hashes, OCR strings, and original task outcomes are consumed from A09 raw, not edited here.

No test-double action sends GUI input. The `unavailable` Submit-effect verdict is fixed and is not evidence about an application.
