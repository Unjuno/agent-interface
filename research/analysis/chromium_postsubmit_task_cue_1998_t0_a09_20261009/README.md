# A09 post-submit pending-effect OCR cue

Allocation `LABEL-CONTROL-AMBIGUITY-1998-T0-A09-20261009` tests whether a fixed, byte-saving A04 crop can recover the exact task token from Chromium epoch 8, after the submit action but before the retained public-effect acknowledgement. It is separate from A06's pre-submit epoch-7 allocation. The pre-allocation full-frame OCR pilot is preserved byte-exact under `preflight/`; it missed exact token `t001101`.

Formal candidate input is restricted to the 20 fixed A04 crop PNGs. It does not rerun the full-frame pilot or any GUI/task. Candidate and independent auditor each run once after freeze; no retries. Scope is one retained frame and deterministic Tesseract extractability only.
