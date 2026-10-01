# Scale-aware pixel reference return — first frozen result

## Disposition

**HOLD_MATCHER_RANGE.** Issue #729, task `MAP01-SCALE-REFERENCE-RETURN-20260917-001`. Ten fresh real X11/MAP01 sessions completed once. Scale support enabled one large-offset return that translation-only matching could not initiate, but a second scaled case stopped after one correction because an intermediate view failed the unchanged correlation threshold. The four-scale candidate does not pass the frozen promotion gate. No threshold relaxation, replacement, continuation of failed cases, or runtime promotion occurred.

Publication BASE `a4538c1edcaa8fb6a9305c303fa76c70561ffed9`. Source freeze `80a8f12ff28f9409da757ed700e8ead93b4bd9e5`; source text blob `7ccb968f5580f119fc01a5405eddb52d5f5869de`, 17,113 bytes. Decoded source archive SHA-256 `80e41afabb624b2534f2c0f5614ce8f98e8c1e473aba86feae3ccf9c1edbf4ff`, 12,832 bytes. Eleven exact source/plan/environment files plus FREEZE.json were published and their Git identity read back before any new live case.

## Issue alignment and separation

This follows #480's bounded local-policy/termination question and #59/#105's one-factor real-time-control ladder. #57 requires integration-relevant blockers, not endless isolated features. Read the newly retained #710 before choosing this rung: its raw RGB stop predicate sometimes rejected an already task-valid view and continued away. This study does not rerun #710 or replace its result. It tests the separate reference-patch construction predecessor, whose large-offset translation matcher failed and whose four-scale repair was only posthoc.

The predecessor archive `map01_pixel_reference_return_v1_evidence.tar.xz` is SHA-256 `740205e1d46c615b4546c29ac3f0c543760b022a8d2c1fa13f58f88b264f2bf2`. Its two construction outcomes and unstarted fourteen-case formal plan remain historical. The current ten cases have new IDs and new sessions, and are not pooled with them. The starting scene, ROI and scale set remain development-known: this is fresh-session validation, not held-out scene/semantic target validation. Active #626/#629 and device/feedback paths were not modified.

## Frozen H / T / D / C / U

**H:** adding only the fixed template scales 1, 1.25, 1.5, 1.75 improves safe reference return across a larger authored yaw disturbance without weakening the score, ambiguity, input or terminal gates.

**T:** two seeds 996910/996911, two Right setup dwells 190/350 ms, two matchers translation/scaled = eight cases, plus scaled already-aligned and flat-reference controls = ten. Counterbalanced order; no new live construction; static/image tests before remote freeze. One private Xvfb/Openbox/ViZDoom session per supervised container invocation, exclusive consumption markers, no reruns/replacements/extensions. Input owner and motion commands are unchanged. Reference ROI (278,206)-(342,250), grayscale/downsample by two, NCC >=0.80, uniqueness margin >=0.08 outside a 20-source-pixel horizontal exclusion, centering within12 source pixels, two consecutive centered images separated by >=100ms. Corrections are40ms Left/Right plus100ms settling; maximum24 pulses/6s loop. Parent/evaluator and process deadlines are independent. A blocked X11 call is not a hard real-time proof.

**D:** PASS requires scaled4/4 main returns with VISUAL_ALIGNED and independent reference-yaw error <=3deg, translation small2/2 returns, translation large misses at least1/2, both control conditions correct with zero input, and all identity/input/release/evidence gates. A false VISUAL_ALIGNED stops the block as FAIL; integrity contradictions stop as FAIL; ordinary safe abstention is retained and remaining scheduled cases continue. Scaled large1/2 did not return, so the frozen result is HOLD_MATCHER_RANGE.

**C:** fixed isotropic scale support may cover initial and terminal views while leaving intermediate perspective states unmatchable. Similar pixels are not semantic object identity. Different host/input scheduling may make a40ms pulse cover one or two game updates, sampling or skipping such a state. No claim of a unique lost-event or rendering cause follows.

**U:** one host/backend and development-known map/ROI. Two seeds per disturbance are a finite diagnostic, not a population reliability estimate. Game state is evaluator-only and never supplied to the controller. Source/process-interface separation is not a hostile-process security sandbox. Calibrated combined uncertainty u_c and coverage factor k are unavailable. No fixed-macro superiority, model/token benefit, survival/navigation effect, MAP01 clear, exact-angle guarantee or production claim.

## First outcomes

All yaw values below are evaluator-only absolute wrapped differences from the case's own reference, stored in degrees.

| Case | Matcher / condition | Initial yaw error | Terminal | Correction pulses | Final yaw error |
|---|---|---:|---|---:|---:|
|00|scaled/aligned|0|VISUAL_ALIGNED|0|0|
|01|translation/small|15.8203|VISUAL_ALIGNED|6|0|
|02|scaled/small|12.3047|VISUAL_ALIGNED|3|1.7578|
|03|scaled/large|33.3984|VISUAL_ALIGNED|14|0|
|04|translation/large|33.3984|NOT_FOUND|0|33.3984|
|05|scaled/small|15.8203|VISUAL_ALIGNED|4|1.7578|
|06|translation/small|15.8203|VISUAL_ALIGNED|6|0|
|07|translation/large|33.3984|NOT_FOUND|0|33.3984|
|08|scaled/large|33.3984|NOT_FOUND|1|31.6406|
|09|scaled/flat reference|0|UNKNOWN_REFERENCE|0|0|

Scaled main task returns3/4, translated main2/4; this descriptive contrast does NOT satisfy the predeclared all-scaled gate. Both matchers return in all small cases; translation rejects both large cases without input. No false VISUAL_ALIGNED outside3deg occurred. Both controls use zero correction input. All10 cases pass frozen integrity, all62 non-vacuous owner-release records verify empty,50 observation decisions were recomputed independently, and90 PNGs are retained. All health samples are100 and positions unchanged; there is no threat/survival exposure.

Do not call fewer small-case pulses a speedup. Case02 began at a different yaw despite matched requested disturbance, and four-scale evaluation has greater computation cost. Successful scaled large control took4.680s; its failed matched large control took0.618s before safe stopping. These are individual diagnostic times, not a matched latency benefit.

## Concrete failure and posthoc path diagnosis

Cases03 and08 both start at33.3984deg and with scale1.5 NCC0.841841315, uniqueness margin0.194518447. The first40ms correction does not induce the same observed intermediate view. Case03 next samples29.8828deg and matches at scale1.25 with NCC0.839940687, then eventually returns. Case08 next samples31.6406deg; its best four-scale match is NCC0.797426501, margin0.144895003, scale1.5. Score fails0.80 although uniqueness passes. The controller issues no second correction and correctly reports NOT_FOUND, not task success.

The corresponding parent samples before capture start and after capture end have identical yaw for each of these frames. `posthoc-path-bracketing.json` retains the brackets. This is posthoc sampled-state evidence, not exact camera-exposure or native-event-consumption timing. The complete RGB frames are not byte-identical at the initial states even though best-match values and yaw agree.

**Inference:** a successful trajectory can skip a state where the same frozen observation rule would stop. Starting-view acquisition plus terminal-view recognition is therefore insufficient evidence of closed-loop observability along the path. A longer pulse that happens to skip the bad state is not a justified repair. Neither threshold lowering nor extra scales were tested after this result.

## Integrity and reproducibility

Unit tests16/16 before and after measurement. Four known-predecessor-image crosschecks verified the separately coded auditor before freeze; they are not held-out cases. The auditor uses explicitly mean-centered candidate vectors, rather than the implementation's variance identity, to recompute every match and subsequent action. It independently checks source/image identity, schedule, controller-file binding, input subset/dwell, authority ordering, non-vacuous final release, independent X11 keymaps, terminal effect and process cleanup.

Six postformal copied-evidence mutations all reject without auditor crashes: altered match center, changed PNG byte, contradictory key bitmap, invalid lease deadline, removed final-release record, and false VISUAL_ALIGNED on the failed case. A final process check found no remaining ViZDoom/Xvfb/Openbox/input-owner process. There was no live rerun for verification. This is self-audit and mutation testing, not third-party review.

## Variables and dimensional check

| Field | Meaning (Japanese) | SI unit | Definition | Range/assumption | Type |
|---|---|---|---|---|---|
|ROI|参照画素領域|1; digital px|fixed source rectangle(278,206,342,250)|640x480 observed image|integer vector|
|score|正規化画像相関|1|centered template/candidate dot product divided by both norms|-1..1; nonflat reference|real scalar|
|margin|別候補との差|1|best score minus best outside20 source px|admit >=0.08|real scalar|
|scale|参照画像の拡大率|1|fixed template resizing factor|1,1.25,1.5,1.75|real scalar|
|error_x_px|元の横位置との差|1; digital px|matched center minus310|centered when absolute error<=12|real scalar|
|pulse_seconds|入力保持要求時間|s|0.04 per correction; setup0.19/0.35|positive; native lease bounded|real scalar|
|capture/decision ns|観測と判断の時刻|s; integer ns|perf_counter_ns in a shared monotonic domain|ordered timestamps; not calibrated accuracy|integer scalar|
|yaw error|評価専用の方位差|rad; stored deg|minimum absolute circular difference from reference|0..180deg; never controller input|real scalar|
|pulses|補正入力数|1|audited key-down/up cycles|0..24|integer scalar|

Centered-intensity dot product and the norm product have the same squared-intensity dimension, so their ratio and margin are dimensionless. Downsampled centers are converted back to source pixels before comparing with12px. Nanosecond intervals are converted to seconds for6s bounds. Angular errors and the3deg gate use the same unit. A1ns clock resolution is not1ns measurement accuracy; digital pixels are not meters.

## Environment

AMD EPYC9V74 80-Core Processor; affinity CPUs0..4; host clock/frequency uncontrolled. Linux6.18.44 x86_64/glibc2.41, CPython3.13.5, ViZDoom1.3.0, NumPy2.5.3, Pillow12.3.0, python-xlib0.33. Xvfb/Openbox private1280x800x24, game640x480, ASYNC_SPECTATOR35tics/s, normal MAP01 skill1, cl_run=false. One serial game; separate pixel controller/evaluator; NumPy/OMP threads limited to1. No GPU claim. Previous Intel-host construction timings are not pooled.

Offline runtime artifact10398313098, ZIP SHA256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`, remains BASE9e6d5ecd, not moving main. All2592 source SHA256/Git identities and12 wheel hashes were verified, then complete wheels installed offline. Input adapter common.py is unchanged at Git blob `d349f0f303c829b8dee8a6543bc9ee83b31ae5ba`. API references checked: official NumPy sliding_window_view reference and Farama DoomGame documentation. Observed pinned binaries, not current documentation alone, define this experiment's implementation.

## Retention and one successor

GitHub retains the exact premeasurement source archive, report, compact summary/decision witness and posthoc read-only restoration helper. The complete90 PNGs, original input/evaluator/controller JSON, invocation receipts, audits and logs are in the separately delivered full-evidence archive identified by PUBLICATION.json. The compact witness alone does not verify image pixels or native input receipts. Full frozen audit requires the complete archive and pinned Python dependencies.

Next discriminating question: can a single task-relative geometric observation model maintain a unique reference match at the failed intermediate view and adjacent views without widening the acceptance threshold? Test this observation boundary without input before a new closed-loop allocation. Do not repeat successful paths until the failed intermediate state disappears from the sample.
