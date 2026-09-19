# Pixel-only return-view stopping: HOLD, not promotion

Issue #710; task MAP01-PIXEL-RETURN-STOP-20260917-001. Publication BASE `65c096610dbcbe63c7a3e649af2665954a1bfb12`; source-first commit `ee625aababf221b7087b977b396c3aff4e7e5f93`. Only this new research namespace changes. #480/#59/#105/#57/#701 motivated the local termination gate; #626/#629 and other worker paths remain untouched.

## Frozen experiment

H: the same bounded six-pulse return macro can avoid unnecessary correction by stopping from current X11 pixels matching its session-local reference view. T: two seeds, three authored Right-pulse perturbations (1/3/6), two correction policies, plus two already-aligned and two missing-reference candidate controls: 16 fresh normal-MAP01 sessions. Two nominal construction sessions are excluded. No formal rerun/replacement/extension/tuning.

Both policies capture and score the same current-image predicate. Fixed executes six Left90ms pulses with100ms settling; pixel_stop may terminate earlier. Both have the same three-second horizon and abstain on unavailable/low-contrast images. The dimensionless RGB MAE is measured in ROI [160,120,480,260], divided by255, with frozen threshold0.035. The controller is a separate process and receives no game angle, action state, health, seed or perturbation count. The independent scorer uses wrapped camera-yaw error <=6 degrees; image similarity is not semantic object identity.

D required all six main candidates within that angular tolerance, fewer than six correction pulses on all four lower-displacement cases, usable nominal baseline, discriminating lower-displacement baseline failures, no false MATCHED and correct negative controls. Integrity violations stop the block. A negative scientific result is retained without changing the predicate.

## First result: HOLD_TARGET_NOT_REACHED

All16 integrity audits pass with0 errors. Candidate geometric goal4/6 versus fixed2/6 does NOT pass the preregistered gates. Only2/6 main candidates explicitly report MATCHED; four exhaust the six-pulse budget, including two that finish inside the independent tolerance without recognizing it.

| Right setup pulses | Fixed terminal error (2 cases) | Pixel-stop terminal error (2 cases) | Candidate outcome/pulses |
|---|---|---|---|
|1|28.125 /28.125 degrees|0 /0 degrees|MATCHED /1 each|
|3|15.82031 /15.82031 degrees|19.33594 /17.57813 degrees|BUDGET /6 each|
|6|3.51562 /3.51562 degrees|3.51563 /1.75781 degrees|BUDGET /6 each|

Nominal fixed baseline2/2 succeeds; lower-displacement baseline4/4 misses. Lower-displacement candidate early stops2/4, not the required4/4. Both aligned controls MATCHED with0 correction; both missing-reference controls UNKNOWN with0 correction. No false MATCHED outside6 degrees. All health remained100; no death or MAP01 exit. Counts are finite diagnostic coverage, not reliability estimates.

## Posthoc diagnosis, not a retuned gate

Case-02 step3 has equal bracketing evaluator yaw samples at3.515625 degrees from reference, but raw MAE0.05360285 exceeds0.035. It continues to19.33594 degrees. Case-09 step3 similarly has yaw error1.7578125 degrees and MAE0.04465911, then finishes17.57813 degrees away. All78 decision captures have equal-yaw bracketing samples in retained posthoc analysis. These brackets are not exact render/event-consumption timestamps.

Thus the current-image proxy rejects an already acceptable task-relative view, and authorized continuation moves away. This is a stopping-contract mismatch, not an authority expansion. Do not solve it by feeding evaluator angle to the controller or retuning on these cases. The next question is task-relative geometric image correspondence with the motor limits and independent scorer held fixed, not another duration/threshold sweep or a macro DSL.

## Checks and environment

Frozen11 input hashes unchanged; unit tests8/8 before and after.134 explicit non-vacuous owner-release records verify; independent initial/precontrol/final X11 keymap checks are empty.110 formal PNGs and18 construction PNGs retained. Six copied-evidence corruptions reject action-key, bitmap, missing-release, MAE, deadline and PNG-digest contradictions. Fresh full-archive extraction verifies314 manifest files and reproduces the frozen audit and original numerical replay byte-identically without live reruns.

Intel Xeon Platinum8370C; CPU model label2.80GHz is not controlled operating frequency. Affinity0..4; Linux6.18.44/glibc2.41; CPython3.13.5; ViZDoom1.3.0; NumPy2.5.3; Pillow12.3.0; python-xlib0.33; Xvfb21.1.16/Openbox3.6.1. Private1280x800x24 desktop,640x480 game, ASYNC_SPECTATOR35tics/s, skill1, cl_run=false. One serial session per outer call. Executed runtime remains artifact10398313098/base9e6d5ecd, SHA256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`;2592 source identities and12 wheels verified. No comparison to prior EPYC timing is justified.

C/U: animation/lighting, pixel aliasing, pulse granularity and shared-host scheduling remain. A camera-reference task is not semantic reacquisition. No model selection, token savings, speedup, threat/survival benefit, MAP01 clear or production promotion. Calibrated combined uncertainty and coverage factor unavailable; image MAE (unit1) and angle (rad, stored degrees) are distinct quantities, not interchangeable units. Full variable definitions and unit check are in the packed detailed report.

## Actual publication layout

`source.tar.xz.b64` is the unchanged premeasurement source archive. `evidence.json.xz.b64` losslessly packs the detailed report text, parsed frozen RESULT values, all16 numerical case witnesses using float.hex() yaw, original result hashes, freeze and corruption checks, and two selected posthoc brackets. `replay.py` is a postmeasurement standard-library-only numerical verifier; it does not re-execute gameplay. Run `python replay.py`; `python replay.py --extract NEW_DIR` also restores the exact detailed report and parsed result values. It refuses an existing directory.

The detailed report inside the full archive anticipated loose RESULT/witness filenames. The actual GitHub layout is the packed layout above: result values are lossless, not a claim of original JSON key-order/whitespace reconstruction. Numerical replay cannot verify native receipts, image pixels or process cleanup.

Complete source/raw input/PNG audit requires the conversation archive `map01_pixel_return_stop_v1_evidence.tar.xz`:7,018,452bytes, SHA256 `5d735664fe5b7f80bc6756df930d15d2e18f7d27aa8b75ae770b9a7c28d7c149`. Full audit command after extracting the archive: `python source/audit.py formal source` with its pinned dependencies. All128 PNGs and process logs are NOT claimed as GitHub-retained. No third-party review or CI success is asserted by the local checks.
