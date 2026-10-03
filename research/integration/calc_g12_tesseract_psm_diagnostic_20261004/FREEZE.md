# Frozen post-run OCR segmentation diagnostic

This is a read-only diagnostic on the known G12 post-action crop, not a new
GUI/model experiment and not a regrade of G12.

- **H:** Tesseract page-segmentation choice may explain part of the retained
  `951` result for an image that visibly contains `551`.
- **T:** Run one process each at PSM 6, 7, 8, 10 and 13 on the exact retained
  C2 crop. Keep language `eng`, the digit whitelist `0123456789`, image bytes,
  binary and all other options fixed. PSM 7 is the same-mode control on this
  host; the original run used a separately pinned container image.
- **D:** Exact stdout `551` identifies a candidate mode for later validation;
  no exact match means this finite mode set does not repair this crop. This
  rule applies only to this known image.
- **C:** Any match may fit this one known value. It does not establish OCR
  accuracy on unseen numbers, another font, or another platform.
- **U:** One known crop, one run per mode, host macOS Tesseract 5.5.2. No GUI,
  model, native input, task completion, or efficiency measurement.

Input: `input-c2.png`, copied byte-for-byte from PR #7198 head
`5a19c8b40ebe5639ac5abfebcf2a6cdedf42556c`, path
`calc-measured-boundedread-4d74/runs/measured_boundedread12/ocr-fc18f31a2b09407fb697238ec8f9ddac.png`.
The source file is 5,189 bytes, SHA256
`851ad8686d681fe55aaa6ac8c609e67f47812334d8ded79658434e94ff8445f8`,
392×96 pixels. The raw G12 transcript records PSM 7 returning `951` for this
crop. The expected visible string `551` is used only for post-call
classification, never passed to Tesseract.

Pre-run environment: macOS 27.0.1 arm64; Tesseract 5.5.2 with Leptonica
1.87.0. `tesseract --help-psm` confirmed the selected modes. No package or
runtime installation was performed.
