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

## Retained-pixel timing check

The A04 source commit also retains the original Chromium trace frames and action record. A visual read of the immutable epoch-8 frame (`research/observation_gating/results/baseline-screen-02/chromium-1101-O0/frames/36563401256d29715e9ef9b1ceadd4f0764b78712dc9b62d5578283e35e40d06.png`; observation sequence 8) shows `FORM READY` and the input appears to contain only the prefix `t0011`. This was the selected post-submit frame; its capture precedes the recorded public-effect-known time. The next retained observation, sequence 9 (`.../frames/8f9f1351d7c90cb9e6579e66ccc9db33bbe95cca6d89504972ce5d52d91d4d34.png`), shows `FORM SAVED` and the full `t001101`. The task oracle independently records the submitted and actual value as `t001101` and success.

The action trace places `type_token` input acknowledgement at 17.316 ms and its first-feedback timestamp at 30.430 ms after issue; `submit` was issued at 30.444 ms after the type action issue. This is consistent with the chosen epoch-8 frame capturing a transient, incomplete visual value, followed shortly by a successful full submission. It does not prove that input injection itself was incomplete, and human visual reading of the small field is qualitative. The exact A09 OCR finding remains valid, but this timing check means it should not be interpreted as a crop/OCR failure on a frame that visibly contained the full target token. This check uses only retained images and logs; no task replay, GUI interaction, or OCR was run.
