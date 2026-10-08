# FFmpeg outcome transfer: stop requested does not mean effects stopped

Decision: RETAIN the three-layer result candidate for the declared export predicate. Issue #232. Publication base bb73e70471cc769501fdca7f2eb4aaa4f3f39d55; premeasurement freeze b8d2dbaf1e2a61635bc851389b4d651108ea8938. Only additive research files, no runtime/workflow/historical-result changes.

## Discovery and scope

The prior Doom work separated motor completion, episode termination and goal success. This transfers that conceptual distinction, not the same production implementation, to unmodified native FFmpeg launched by XTEST Return in native xterm. No model, network service, user-data operation or new Doom episode.

Goal: initially absent per-case output.png must be 96x64 and contain exact declared RGB bytes after the sole FFmpeg producer is reaped. The generated FFV1 clip is two seconds/20 identical frames. This is an authored, independently decidable artifact goal, not semantic recognition of arbitrary tasks.

Six direct construction checks exposed code-zero/no-output after a beyond-end seek and a PNG appearing during SIGTERM shutdown. Two further signal checks discriminated graceful versus hard stop. These checks are retained but excluded from estimates. The frozen allocation used seven conditions, three repeats, shuffled per block with seed232916. All21 ran once; no consumed IDs rerun.

## Native results

| Condition | Intervention | Native return code, each of3 | Exact image /3 |
|---|---|---:|---:|
| Exact | first frame PNG |0|3|
| Beyond end | input seek3s on2s clip |0|0; absent|
| Wrong size | scale48x32 |0|0; wrong image|
| Missing | absent local input |254|0|
| Graceful stop | real-time input, select frame15+, SIGTERM at800ms |255|3|
| Hard stop | identical delayed-frame job, SIGKILL at800ms |-9|0|
| Trailing output stop | first PNG plus remaining video to null output; SIGTERM at800ms |255|3|

These are deliberately authored command conditions, not alleged FFmpeg bugs or naturally sampled agent errors. Negative return codes use Python's local signal-termination representation.

Three result rules are evaluated on the SAME traces, not three different agent policies:

| Rule | Correct /21 | False success | False negative |
|---|---:|---:|---:|
| Release implies goal |9|12|0|
| Exit zero implies goal |9|6|6|
| Separate input/process/exact artifact |21|0|0|

Actual goal achievement is9/21, not21/21. The first two rules are deliberately simplistic controls, NOT the current product baseline. The candidate consumes additional file/dimension/pixel evidence, so this is not equal-information or speed/agent-performance evidence. It preserves stop_requested and native process status. While the producer runs it returns unresolved even when the current image is exact. After reaping it checks the artifact and returns the observed goal result; it grants no retry or input permission.

## New discriminator: effect after stop

All three graceful-stop cases lacked output at the request and still had post-request absence observations at251.307–256.128ms. A subsequent exact image appeared in all3. From completed signal request to first exact-image observation: median272.380ms, range268.396–272.552ms. To producer reaping: median365.368ms, range362.643–366.162ms.

Hard-stop counterparts had no PNG3/3; reaping after request median10.363ms, range10.349–10.419ms. Trailing-output cases already had the exact PNG722.606–728.458ms before request, and reaped afterward at median376.189ms, range364.121–377.887ms.

Thus identical nonzero255 results hide different effect timing, and cancellation request is neither quiescence nor rollback. These endpoints are sampled observations, not exact write times. Polling is nominal10ms. No particular internal FFmpeg-buffer explanation is established, and no universal recommendation for hard termination follows: other jobs may retain partial effects. No retry was tested.

## Measurement and implementation assumptions

AMD EPYC9V74, affinity CPUs0–4, unpinned/shared-host frequency, batch1/sequential sessions; CPython3.13.5/Linux6.18.44; FFmpeg7.1.5-0+deb13u1; XTerm398; private1024x480x24 Xvfb with NO window manager; XTEST Return20ms, separate X11 connection verifies down/empty; Pillow12.3.0 candidate. Xlib module reports [0,15]; package metadata lookup was unavailable, not guessed. FFmpeg decoder/encoder thread settings1 are explicit in retained argv. Input harness is NOT production Executor/InputOwner. No power-loss durability or whole-system/ABI integrity claim follows from executable hashes.

Two GUI preflights failed before input: premature focus on a non-viewable window, then unmapped xterm under private Openbox despite checking viewability. Separate no-input diagnostics isolated this. The scored setup omits the window manager and checks mapping/focus. A third separately named successful preflight supplies only offline mutation-test data. All earlier sources/errors remain retained.

Persisted semantic payload and delivered payload match exactly by type; transport emitted_ns lives outside that payload. No broad whole-dictionary exception hides changed semantic fields.

## Verification

The frozen auditor was unchanged after measurement and passes21/21. It validates1022 acquisition brackets, all21 press/release/final-empty checks, all argv and run identities, final artifacts, and42 full screenshot RGB hashes. A separate standard-library PNG reader implements CRC checks and filters0–4; it imports neither candidate classifier nor Pillow/FFmpeg decoder. Twelve output PNGs exist:9 exact and3 wrong-sized.

37 tests passed before execution and again from independently extracted evidence:24 contract/PNG tests and13 real-preflight mutation tests. Re-extracted replay reproduces all21 result rows exactly. All569 manifest files (1498218 bytes) match. Neither individual polls nor repeated known scenarios are independent application samples.

## H/T/D/C/U and transfer

H: input release, process status and effect correctness differ; graceful stop can generate an effect after request. T: frozen7x3 native jobs, matched stop-command pair, same-trace result rules, independent output decoding. D: scoped gate PASS; no false result from the separated candidate and all integrity/release gates pass. C: extra evidence explains better classification; authored conditions, signal behavior and single-producer assumptions constrain transfer. U: one host/clip, n3/cell, polling/host jitter, no concurrent external writers or restart/power-loss study; no calibrated combined uncertainty or coverage factor.

Related fields: operating-system process lifecycle, distributed request/acknowledgement/effect handling, and measurement science. The next question is how a consumer recognizes producer quiescence before retrying, not how to rename every nonzero exit as failure.

Units: start/end/reaped timestamps use same-host perf_counter_ns integers; differences divided by1000000 produce milliseconds. Pixel dimensions and return codes are dimensionless. Resolution is not accuracy. Recorded run_id is a string binding one artifact/process/input set, not an authenticated identity; goal_met is optional Boolean and remains unknown before final evidence.

## Retention

All exact executable sources, full frozen plan and full result rows are in the three-part source bundle; details in README.md. Full raw evidence is a conversation attachment ONLY, NOT uploaded to GitHub/Actions: ffmpeg_outcome_evidence_20260916.tar.xz,211424 bytes,SHA256 00cb644b00df06875d0ab99d6a40582d3e03c5327d69f5561be9a1181d8f12eb. User ZIP748964 bytes,SHA256 255af116d5e8fba65c8619df7b1cae14cfc7c857e026d4a768ca698d4f11dd2b. The raw archive contains a longer report, all errors and original evidence. No fonts or OS/application binaries are distributed.

Primary implementation references: official FFmpeg command reference and FAQ at ffmpeg.org; Python subprocess documentation at docs.python.org. Measured conclusions are version-pinned, not inferred from newer documentation.
