# A05 raw-crop pixel identity audit

This read-only audit checks whether the six retained 4× crop previews used by
the post-hoc OCR check reconstruct from their SHA-pinned A05 source frames, and
whether each frozen crop preview contains the exact pixels from the archived
`ocr-*.png` input used by the original comparison. It does not invoke OCR or
rerun any A05 arm.

## H/T/D/C/U

- **H:** the previews reproduce the pinned source crops, and the three frozen
  previews are pixel-identical to their archived runtime OCR inputs.
- **T:** reconstruct all three frozen and all three padded candidates from
  source frames pinned to revision `58bcbb4c45501880db8782158ddd3add3b765984`;
  require the exact six expected `(block, task, crop)` entries; check source,
  preview, and historically pinned archived-OCR SHA-256 values; then compare
  decoded RGB pixels for each frozen preview against its archived OCR input.
- **D:** PASS only if all six preview files reconstruct byte-for-byte and each
  archived OCR input is pixel-identical to its frozen preview. PNG serialization
bytes may differ if decoded pixels match.
- **C:** a Pillow version difference, color-mode conversion, or resize behavior
  could change reconstructed pixels; a preview manifest may also identify a
  different source than the archived OCR input.
- **U:** this audit establishes input-pixel identity only. It does not explain
  why historical stdout omitted the leading `t`, qualify OCR false acceptance,
  or establish a live observer or GUI effect.

## Result

The audit reconstructed all six previews byte-for-byte with Pillow 12.3.0.
Each of the three archived frozen-crop OCR inputs is pixel-identical to its
corresponding preview, although the PNG file hashes differ. Therefore the
Tesseract 5.5.2 outputs recorded in [PR #7628](https://github.com/Unjuno/agent-interface/pull/7628)
apply to the exact frozen-crop pixels from the original A05 run. The historical
leading-character discrepancy remains an OCR environment or execution-record
attribution issue; crop-preview mismatch is not supported by these pixels.

PR #7628's padded-crop positives and one-character expected-token substitutions
are retained diagnostics, not false-accept image controls. This audit does not
upgrade its disposition or change A05's formal 9/12 result. No OCR, GUI, model,
live runtime, or formal allocation was run.

## Reproduction

From the repository root:

```sh
python research/integration/a05_ocr_raw_pixel_identity_audit_20261005/audit.py
```

The command writes `AUDIT.json`. The pinned source hashes, preview hashes,
archived OCR hashes, decoded pixel comparisons, and runtime versions are
recorded there. Two regressions reject a truncated/duplicated manifest and a
same-pixel OCR image with different bytes. `SHA256SUMS` covers this package.
