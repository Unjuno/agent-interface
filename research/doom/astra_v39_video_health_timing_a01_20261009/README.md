# Astra retained-video health timing A01

This is a post-hoc reconstruction of health values around Astra decision 4's
slow response. It adds timing evidence to the retained failure record; it does
not establish what a current V39 guard would have done.

## Question and frozen test

**H:** the retained 2× video and exact captured frames can locate visible health
changes around one recorded model-response interval closely enough to determine
whether a hypothetical guard threshold was crossed before the controller's
recorded response end.

**T:** on then-current main commit `0455b0079ca29bcfe85153f280e592f5e96528f6`, decode the
hash-bound 780-frame MP4 once. Match exact source captures at sequences 117,
148, and 211 against the video, read the 85 frames from 22.0 through 30.4 video
seconds with the current-main WAD-template reader, and linearly map
`capture_ns` onto video time. An independent scalar pixel scorer, separate WAD
parser, and decoder then reconstruct the rows and anchor matches.

**D:** `PASS_POSTHOC_EXTRACTION` requires 85/85 observed rows, each anchor below
2.5 mean absolute pixel error, and no nonlocal match within 0.05 error of an
anchor's best match. Otherwise the first result remains HOLD. The 90/88/84/80/78
health-floor sweep is explicitly sensitivity analysis; no historical guard
using those floors was found.

**C:** scene repetition could alias an anchor; video compression could defeat
the exact pixel reader; capture timestamps could differ from video presentation
time; and controller elapsed time may not equal the report's model duration.

**U:** video-to-event clock synchronization remains unknown. The fitted-clock
uncertainty also includes the largest fit residual, half a video frame, and
half the widest local anchor match. That bound cannot settle an ordering inside
the sampled frame interval.

## Result

The one frozen candidate run returned `PASS_POSTHOC_EXTRACTION`: all 85 health
rows were observed, and the independent audit returned `PASS_AUDIT` with zero
row or anchor mismatches and all five corruption controls detected. The three
source frames matched video frame 176 (17.6 s, score 1.9984), frames 220–221
(22.0–22.1 s, scores 1.9258–1.9628), and frame 286 (28.6 s, score 1.9544).

Health was 100 at 22.0 s, 96 at 23.5 s, 94 at 27.4 s, 87 at 28.2 s, 84 at
28.5 s, and 83 at 30.2 s. A sensitivity floor of 90 or 88 is first observed
below at 28.2 s, after a 94 reading at 28.1 s. The controller report maps its
recorded end to 28.247 s; the combined mapping allowance is ±0.152 s from the
largest fit residual, half a video frame, and half the anchor-match interval.
That allowance is wider than the gap. The video is sampled at 10 fps and
displayed at 2×, and the unmodeled media synchronization error is unknown. The
order of the health change and response end is therefore **unresolved**.

The report records `model_ns=11.741060121 s`; its controller start/end fields
span 11.844595127 s, a 103.535006 ms difference the report does not explain.
Both measurements are preserved. The floor sweep is not an authored controller
policy and cannot demonstrate a guard firing.

## Scope and next gate

This is host-only offline image analysis. It made no game or GUI connection,
model call, OS input, key release, or task action. It does not satisfy the fresh
current-main threat-control gate. The one-shot live result in [PR #8678](https://github.com/Unjuno/agent-interface/pull/8678)
did not cross the authored hard-health floors and ended with a failed cover
cancellation and incomplete cleanup; it was not retried. The cancellation
repairs are under review in [PR #8683](https://github.com/Unjuno/agent-interface/pull/8683)
and [PR #8684](https://github.com/Unjuno/agent-interface/pull/8684). Latest main
`743ae74e` also contains a synthetic `FAIL_METHOD` showing that duplicate
cleanup event IDs can hide an unmatched acceptance and make empty-release
reconstruction order-dependent; it does not show that production emits these
duplicates. A new live allocation must wait for the repair path and duplicate
identity handling to be reviewed, then test a deliberate authored-floor
crossing, per-key release, useful feedback, bounded recovery, and terminal task
outcome under a newly assigned lane.

## Reproduction and files

`FREEZE.json` pins the source commit, MP4, event stream, decision report,
three source frames, reader modules, runtime, FFmpeg, WAD, candidate, and
auditor. `CURRENT_MAIN_CONTINUITY.json` records that all seven relevant input
and reader blobs remain unchanged on later main `743ae74e`; the candidate was
not rerun. The WAD was obtained from the [official ViZDoom source](https://github.com/Farama-Foundation/ViZDoom/blob/main/src/freedoom2.wad)
and matched the repository's existing SHA-256 pin. `PREFLIGHT.json` preserves
the exploratory prerequisites; `RUN_RECORD.json` distinguishes recorded
artifact times from the missing exact invocation start time.

The preserved candidate and audit results, first-run stdout/stderr/exit codes
are under `results/`; `SHA256SUMS.txt` covers the package files. Neither the
candidate nor the auditor was retried. Reproduction command lines and host
details are in
[`RUN_RECORD.json`](RUN_RECORD.json).
