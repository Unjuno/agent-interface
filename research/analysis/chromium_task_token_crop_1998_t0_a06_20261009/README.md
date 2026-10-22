# A06: pre-submit Chromium token cue in fixed crops

This package records allocation `LABEL-CONTROL-AMBIGUITY-1998-T0-A06-20261009`. It evaluates only the 20 fixed Pillow/A04 crop PNGs for Chromium epoch 7 (`chromium-3ef7a4415c4f`), after `type_token` and before submit. The retained task oracle binds `t001101`; the exact cue is substring `001101`.

The single full-frame Tesseract PSM 11 preflight performed before allocation is a construction pilot only. Its observed stdout is transcribed in `PREFLIGHT.md`; the original stdout bytes were not retained. The formal candidate does not rerun the full frame or that pilot. It invokes the frozen Tesseract executable once per fixed crop. Candidate and auditor each have one invocation; no retries or GUI interaction are permitted.

The decision concerns fixed Tesseract extractability of a six-digit cue in a smaller serialized crop for this one retained pre-submit view. It says nothing about model utility, human readability, adaptive ROI selection, task submission, latency, or product success. The candidate stdout and independent raw-only audit are authoritative; the report preserves the exact resulting disposition.
