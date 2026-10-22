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

The action trace places `type_token` input acknowledgement at 17.316 ms and its first-feedback timestamp at 30.430 ms after issue; `submit` was issued at 30.444 ms after the type action issue. The exact baseline source shows `Driver.text()` returns only after iterating all characters, with every XTEST key-down/key-up sent by `_raw()` followed by X11 `Display.sync()`. `Observer.action()` records `input_ack_ns` after that call, then immediately samples and returns its first feedback; `first_feedback_is_semantic_completion` is explicitly false. Thus the empty sequence-7 image was captured 5.564 ms after all scripted key events had been synchronized with the X server. This establishes a gap between X11 input-request acknowledgement and visible application state in this trace; it does not establish whether Chromium had processed the full event queue by that capture. The later frames show a partial value and then a successful full submission. Human reading of the small field remains qualitative. The exact A09 OCR finding remains valid, but this timing check means it should not be interpreted as a crop/OCR failure on a frame that visibly contained the full target token. This analysis uses only retained images, logs, and the pinned source; no task replay, GUI interaction, or OCR was run.

### Pixel-only adjacent-frame comparison

To check the visual timing more directly, I inspected the three retained source frames from A04 commit `5d4dbe50bb63a3df19f06b97701bde43217d24af`, without invoking OCR:

| Observation | Recorded pixel digest | Time from `type_token` issue | Input-field dark-pixel bounding box |
|---|---|---:|---:|
| Sequence 7, after `type_token` | `3ef7a4415c4fe589ede0304e00dae19edeefc887e6e3ee73abd24978cb140307` | 22.880 ms | 1 × 15 px (caret only; visually empty) |
| Sequence 8, after `submit` issue | `36563401256d29715e9ef9b1ceadd4f0764b78712dc9b62d5578283e35e40d06` | 37.160 ms | 32 × 15 px (visually partial `t0011`) |
| Sequence 9, saved feedback | `8f9f1351d7c90cb9e6579e66ccc9db33bbe95cca6d89504972ce5d52d91d4d34` | 65.773 ms | 47 × 15 px (visually full `t001101`) |

The boxes were computed from each 1280×800 frame's 140×17 px input-text interior at `[65,236]`, converted to grayscale, thresholded at 50%, and trimmed. ImageMagick 7.1.2-23 produced widths 1, 32, and 47 px. Thus the saved trace has a measurable visual progression from empty, to a prefix, to the full oracle token. The first feedback for `type_token` was the empty sequence-7 frame. Submit followed 13.697 microseconds after its `first_feedback_ns` timestamp (24.155 microseconds after the frame's `ready_ns`). The sequence-8 frame was captured 6.716 ms after submit issue and its OCR was the only one included in the frozen A09 run. The driver source is pinned at baseline commit `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`; the `gui_suite.py` and `real_app_suite_v1.py` Git blob IDs are `d2e62dcbf7f1ec8ff2ecbd41f6f50475b08b5de5` and `080428eaca8b150b9e700de01af8de7326944248`, respectively, and both files are byte-identical in A04 commit `5d4dbe50bb63a3df19f06b97701bde43217d24af`. These post-hoc measurements corroborate the timing qualification but do not establish why rendering/input handling lagged, nor generalize beyond this episode.
