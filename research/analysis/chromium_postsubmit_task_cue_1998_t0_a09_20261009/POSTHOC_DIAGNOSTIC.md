# A09 post-hoc OCR text diagnostic

This note is a descriptive read of the byte-preserved A09 pilot and candidate outputs, after the formal disposition was recorded. It adds no test, OCR invocation, or input to the frozen candidate/auditor run and does not change `FAIL_NO_CROP_TOKEN`.

| Stored output | Crop bounds (pixels) | Payload bytes | Observed OCR text | Exact `t001101` |
|---|---:|---:|---|---|
| Full-frame pre-allocation pilot | full frame | 34,982 | includes `Value [1001]` | absent |
| `a04_16` top-left | `[0, 0, 640, 400]` | 23,627 | includes `Value [1001]` | absent |
| `a12_16` top-left | `[0, 0, 1024, 750]` | 32,457 | includes `Value [1001]` | absent |
| `a12_16` bottom-left | `[0, 50, 1024, 800]` | 29,061 | includes `Value [1001]` | absent |

The full-frame pilot and three stored crop rows with the OCR substring `Value` all report `1001`; no crop row contains the exact task token. The largest listed crop payload remains smaller than the full-frame payload, but this note makes no claim that the crop preserves the token visually or that OCR error is the cause. The retained pixels and OCR strings alone do not distinguish those explanations.

For reproducibility, the candidate output has 20 rows, all with OCR exit 0, and zero rows containing exact `t001101`. These statements are post-hoc summaries of `results/candidate.stdout` and `preflight/full_frame.stdout`; no OCR or GUI was rerun. The formal outcome and its scope ceiling remain those in `REPORT.md` and `RESULT.json`.
