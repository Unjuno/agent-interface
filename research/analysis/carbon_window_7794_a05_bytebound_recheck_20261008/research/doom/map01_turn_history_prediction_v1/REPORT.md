# Source-derived turn-history prediction on held-out MAP01 pulse durations

Task `MAP01-TURN-HISTORY-PREDICTION-20260917-001`, Issue #679.
**PASS_TURN_HISTORY_PREDICTION_HELDOUT_SCOPED.** Ten new private game sessions completed once. The source-derived model predicted all650 consecutive angular increments within its preregistered numerical limits. No fitting, live construction, retry, replacement, extension or threshold change occurred.

## Issue alignment and roadmap

Before measurement this conversation read #480's latest comments, the completed #649 release-gap comparison and its suggested held-out-duration check, plus the #59/#104/#105/#57 sequencing constraints. #626/#629 and mixed-device work were not modified. This is a concrete application-effect prediction gate for #480, not another macro DSL, combat policy or runtime feature.

An earlier independently run local diagnostic `MAP01-PULSE-GAP-VISIBILITY-20260917-001` overlaps #649 scientifically because GitHub writes were unavailable during its allocation. It remains a LOCAL-preregistered diagnostic, not remotely frozen, not pooled with #649 and not rerun here. Its original170-file manifest and retained audit were rechecked; the audit replay was byte-identical. A separate historical publication records that evidence boundary.

Roadmap for this block: read Issues -> reserve #679 -> verify pinned runtime -> parameterize only the pulse duration and neutral controls -> static tests -> remotely freeze source and exact predictor -> execute ten first sessions -> frozen audit -> corruption tests -> publish exact numeric witnesses and full conversation archive -> stop.

## Provenance and implementation assumptions

Publication BASE: `31ae67330ef1739ae45596a2012efe3e942deca3`.
Premeasurement commit: `804f348f9b17f6859ea0dfdf317f421d14e07391`.
Source XZ/Base64 Git blob: `d0131ed17a59209de41bffc4ac3c6ae33440d757`,12953bytes. Decoded source archive:9712bytes, SHA256 `8ae6b51464c7fdb49e0514ba91b478d7396f3d1fec2139911ec7b8e02933ae1b`.

Executed runtime remains offline artifact10398313098 / BASE `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`, ZIP SHA256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`. All2592 source SHA256/Git blobs and12 wheels were checked before complete offline installation. Input adapter `common.py` is unchanged, blob `d349f0f303c829b8dee8a6543bc9ee83b31ae5ba`.

Linux6.18.44 x86_64/glibc2.41; AMD EPYC9V74; affinity CPUs0..4; frequency uncontrolled. CPython3.13.5, ViZDoom1.3.0, NumPy2.5.3, Pillow12.3.0, python-xlib0.33; Xvfb2:21.1.16-1.3+deb13u1, Openbox3.6.1-12+b2. Private1280x800x24 desktop,640x480 game, one serial session per tool invocation, separate actuator and spectator evaluator. Monotonic clock advertises1ns resolution, not1ns accuracy.

Normal MAP01/skill1/ASYNC_SPECTATOR35tics/s. `cl_run=false` is explicitly configured; no strafe/mouse input; source-rule interpretation assumes ticdup1. The source tag agrees with the installed package version but a bit-reproducible engine build was not established.

## H / T / D / C / U frozen before measurement

H: a five-tic low-speed phase followed by the normal keyboard-turn increment predicts new90ms/350ms observations conditional on the evaluator's game-side active/off state. Constant-slow and constant-fast alternatives should fail on their discriminating conditions.

T: one no-input control, four balanced paired seeds994810..994813 at90ms versus350ms dwell, and one final no-input control:10 sessions. Both active conditions have6 Right pulses,5 internal100ms release intervals,120ms initial coast and250ms final sampling tail. No new live construction. Physical input goes through unchanged InputOwner-v10; game action/yaw/health telemetry never enters actuator decisions. No ATTACK, forward, model, direct game action vector, pause, save-state or automap.

D: PASS requires complete identity/input/release/PNG/cleanup audit, consecutive tics,6 separate episodes in all8 active cases, exposure of the appropriate slow/fast regimes, per-tic residual<=0.00001degree, per-case accumulated residual<=0.0001degree, constant-fast error>=1degree in every90ms case, constant-slow error>=1degree in every350ms case and zero-input controls with zero input and total yaw<=0.0001degree. Complete trace contradictions are FAIL_PREDICTION; source/input/evidence failures FAIL_INTEGRITY; omitted/duplicate tics UNCERTAIN_TELEMETRY; inadequate regime exposure HOLD_EXPOSURE. Stop after this block.

C: game-side active/off traces reveal consumed input state, not exact native event-consumption timestamps. Host/SDL/X11 sampling phase changes run lengths. A wall-clock-only model remains a different and untested claim. This test selects a model class; it does not calibrate a usable visual controller.

U: finite single-host diagnostic; matched seeds are not a sample of all schedulers. Both conditions share observer overhead. Combined measurement uncertainty u_c and coverage factor k are unavailable. Numerical residuals below are arithmetic consistency errors, not physical angle accuracy or hardware precision.

## First outcomes

| Seed | 90ms active run lengths in tics | 90ms cumulative yaw magnitude | 350ms active run lengths in tics | 350ms cumulative yaw magnitude |
|---|---|---:|---|---:|
|994810|3,4,3,3,4,3|35.15625deg|13,13,12,12,12,12|207.421875deg|
|994811|3,3,3,3,4,3|33.3984375deg|12,13,13,12,12,12|207.421875deg|
|994812|3,3,3,3,4,3|33.3984375deg|12,12,13,13,12,12|207.421875deg|
|994813|4,3,3,3,3,3|33.3984375deg|12,13,13,12,12,12|207.421875deg|

The90ms arm median is33.3984374deg, range33.3984374..35.1562499deg. The350ms arm median/min/max are207.4218750deg in this four-case block. This equal total is not evidence of general fixed-angle accuracy: pulse-level run lengths vary, and future sampling phase may alter the total. Yaw above180deg is a sum of signed wrapped per-tic increments, not a single final-angle subtraction.

All8 active cases expose6 episodes. All10 cases pass native release and independent initial/final X11 keymap checks;58 owner-release records are non-vacuous and verified. Both no-input controls have0 task downs,0 yaw.20 before/after PNGs are retained.660 sampled tics form650 within-session consecutive transitions, with0 missing/duplicate tics.

Maximum history-model per-tic error:8.340975909959525e-8deg. Maximum accumulated per-case error:7.604285201523453e-8deg. Constant-fast max per-tic error in every90ms case:1.757812583409759deg. Constant-slow max per-tic error in every350ms case:1.7578125008185452deg. All frozen gates pass without fitting.

## Conditional derivation and units

Primary implementation source: ViZDoom1.3.0 `src/vizdoom/src/g_game.cpp`, blob `33722a371dfedaf128dc0b650fac4765576a543f`, definitions of angleturn/SLOWTURNTICS and G_BuildTiccmd/G_AddViewAngle. Official API documentation describes get_last_action as the last performed action, particularly useful in spectator mode.

- https://github.com/Farama-Foundation/ViZDoom/blob/1.3.0/src/vizdoom/src/g_game.cpp
- https://vizdoom.farama.org/main/api/python/doom_game/

| Symbol/field | Meaning | SI unit | Definition/domain/assumption | Type |
|---|---|---|---|---|
| h | Consecutive active-turn counter |1|nonnegative integer;0 on off tic;increment before comparison|integer scalar|
| n | Length of one active episode |1|nonnegative integer number of game tics|integer scalar|
| n0 | Number of initial slow tics |1|5, because source compares incremented h with6|integer constant|
| q_s,q_f | Source slow/normal angle increments |1|320,640 under fixed settings|integer constants|
| B | Binary full-circle denominator |1|65536 after source shift|integer constant|
| pi | Circle constant |1|mathematical constant|real scalar|
| delta_s,delta_f | Per-tic angles |rad|2*pi*q_s/B,2*pi*q_f/B|real scalars|
| theta(n) | Predicted episode angle magnitude |rad|delta_s*min(n,5)+delta_f*max(n-5,0)|real scalar|
| dwell,gap | Requested key-on/off times |s|dwell0.09/0.35;gap0.10|real scalars|
| angle_degrees | Evaluator yaw |rad encoded in degrees|[0,360), adjacent circular difference[-180,180)|real scalar|
| tic | Game update index |1|consecutive integer, nominal35/s|integer scalar|
| timestamps | Local receipt endpoints |s encoded integer ns|same monotonic clock; not native consumption timestamps|integer scalars|

Derivation: while Right is active, the source increments h. For h1..5 it uses q_s; from h6 it uses q_f. An off tic resets h to0. One n-tic episode therefore has min(n,5) slow increments and max(n-5,0) normal increments, whose sum is theta(n). Distinct episodes are summed independently. The predictor begins only from an observed neutral sample and refuses nonconsecutive tics; no alignment offset or coefficient is estimated from outcomes.

Dimension check: q_s,q_f,B,n and h are dimensionless, so both delta values and theta are angles in radians. Timestamps are converted from ns before time comparisons. Request duration is not substituted for game-tic count.

Example in stored degrees:3 active tics yield5.2734375deg;12 active tics yield33.3984375deg. Six12-tic episodes would yield200.390625deg; the actual long cases each have74 active tics over6 episodes (30 slow,44 normal), predicting207.421875deg. This conditional explanation does not predict74 active tics from the350ms request.

## ERROR CHECK and retention

Frozen source hashes10/10; unit tests8/8 before and after. Frozen independent audit10/10,0 errors. Six copied-evidence integrity corruptions were rejected; missing-tic corruption correctly becomes UNCERTAIN_TELEMETRY; altered yaw violates the fixed prediction. No existing raw case was modified. No experiment process remains running.

GitHub numerical witness retains every sampled tic, both action components and every yaw as float.hex(), which round-trips the exact binary64 value, plus each original result-file digest. It permits650-transition numerical replay with no GUI/model call. It deliberately excludes timestamps/native receipts/images/process logs, so `PASS_NUMERIC_REPLAY_ONLY` is not the full frozen audit. Use the separately retained complete evidence archive for source/input/release/PNG/cleanup verification.

To audit an extracted full archive: `python source/audit.py formal source/plan.json`. To rerun static tests: `(cd source && python -m unittest -v test_model)`. Do not rerun consumed formal IDs.

## Disposition and one successor

Retain the source-derived CONDITIONAL effect model; do not promote a100ms default, fixed-angle guarantee, gameplay/controller improvement, model-token reduction or runtime semantics. #480 and #671 remain open. The next useful rung is a bounded pixel-only termination/adaptation test against a fixed macro, retaining hidden game state exclusively for evaluation; stop parameter sweeps here.
