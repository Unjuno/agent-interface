# Issue #8112 — A02 current-main boundary-jitter experiment

Successor to A01 `STOP_MAIN_ADVANCED_BEFORE_CANDIDATE`. A01 invoked neither
candidate nor auditor. This allocation is frozen against its own current main
base and uses a fresh seed; it does not edit or relaunch A01.

## H / T / D / C / U

**H.** On a finite synthetic approach fixture with irregular timestamps,
independently randomized ±1–3 px apparent-radius boundary jitter can reduce or
eliminate secant-TTC's ability to detect contact at least 100 ms early compared
with pixel-change and relative-area-growth thresholds at the same false-YIELD
budget. No advantage is assumed.

**T.** Seed 20261010; 36 opaque-ID 256×256 PGM sequences, 5 frames each,
contact radius 96 px, timestamps `[0,220,610,1180,1800]` ms. 24 constant-speed
approaches (six each at jitter amplitudes 0, 1, 2, 3 px, independent bounded
per-frame radius offsets) and 12 non-approach controls: stationary size jitter
at amplitudes 1–3 px, camera/background scale, lateral translation, occlusion,
track swap, and timestamp regression. Candidate input exposes only opaque IDs,
timestamps, track IDs, and frame paths. Family, jitter, and contact truth stay
in a separate auditor-only sidecar. Compare inherited #5905 A06 thresholds:
pixel `[50,100,200,400,800,1600,3200,6400,12800]`, area
`[0.01,0.02,0.05,0.10,0.20,0.40,0.80]`, TTC `[100,200,400,800,1600,3200,6400]`
ms, 100 ms lead margin. Candidate source and independent auditor source are
reused byte-for-byte from A09 by frozen SHA-256 reference. Run candidate once;
only after exit 0, auditor once. Retries 0. Network disabled, pinned Python
image, one CPU requested, read-only code/input mounts, distinct outputs.

**D.** First require independent reconstruction of 36/36 rows and rejection
of timestamp- and track-substitution mutations. `H_PASS_SCOPED` only if TTC
strictly exceeds both simple-cue frontiers at one or more matched false-YIELD
budgets. Otherwise report `NO_INCREMENTAL_VALUE` (or
`NO_TTC_ADVANTAGE_UNDER_JITTER` if the specific TTC criterion fails). Any
protocol/integrity failure is STOP/FAIL. Preserve first outcomes and exact
invocation counts.

**C.** Rasterization and deterministic 2-D geometry may dominate jitter;
simple cues may suffice; stationary jitter may trigger false positives.
Synthetic frontiers are not deployed-controller costs.

**U.** No real optical flow, target tracking, DOOM, GUI, task effect, model
latency, physical key release, recovery, survival, or safety claim. Pixel
boundary jitter is not calibrated sensor noise.

## Execution gate

Construction base: `cd3a410a930e5f1e29a22cee36d9a149fbc106c7`.
Immediately before candidate invocation, require both `origin/main` and the
branch merge-base to equal this SHA; otherwise record STOP and invoke neither
formal role. Container: locally cached Python image pinned by digest in
`FROZEN.json`; `--pull=never`, `--network=none`, read-only rootfs, CPU=1 and
memory=1g requested (enforcement not asserted). Candidate cannot mount truth.
