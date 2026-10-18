# A09 result: FAIL_NO_CROP_TOKEN

The full-frame pre-allocation pilot exited 0 but missed exact `t001101`. The frozen candidate then OCR-processed all 20 fixed, strict-byte-saving A04 crops for Chromium epoch 8. Every OCR call exited 0. The independent raw-only auditor passed custody and all six mutation controls with zero errors, but found no crop containing exact case-sensitive token `t001101`.

Disposition: `FAIL_NO_CROP_TOKEN`. Candidate/auditor invocations were 1/1, Tesseract crop calls 20, retries 0. The tested fixed crops did not recover the token after submit and before the retained public-effect acknowledgement. This differs from A06's pre-submit epoch-7 screen; A06 remains unchanged.

Scope ceiling: one retained Chromium observation, one exact token, fixed A04 crops, and Tesseract 5.5.2 PSM 11. This is not evidence about human readability, model utility, adaptive crop selection, task success, GUI runtime behavior, latency, or product capability.
