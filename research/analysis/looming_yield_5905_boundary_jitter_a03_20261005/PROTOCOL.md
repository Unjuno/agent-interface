# Issue #8112 — A03 current-main boundary-jitter experiment

Fresh successor to A02 `STOP_MAIN_ADVANCED_BEFORE_CANDIDATE`; A01 and A02
formal invocation counts remain 0/0. Neither stopped allocation is relaunched.

## H / T / D / C / U

**H.** On a finite synthetic approach fixture with irregular timestamps,
independently randomized ±1–3 px apparent-radius boundary jitter can reduce or
eliminate secant-TTC's ability to detect contact at least 100 ms early compared
with pixel-change and relative-area-growth thresholds at the same false-YIELD
budget. No advantage is assumed.

**T.** Fresh seed 20261011; 36 opaque-ID 256×256 PGM sequences, five frames
each, contact radius 96 px, timestamps `[0,220,610,1180,1800]` ms. 24
constant-speed approaches (six each at jitter amplitudes 0, 1, 2, 3 px, with
independent bounded per-frame radius offsets) and 12 non-approach controls:
stationary size jitter at amplitudes 1–3 px, camera/background scale, lateral
translation, occlusion, track swap, and timestamp regression. Candidate input
contains only opaque IDs, timestamps, track IDs, and frame paths; family,
jitter, and contact truth are auditor-only. Compare #5905 A06 thresholds:
pixel `[50,100,200,400,800,1600,3200,6400,12800]`, area
`[0.01,0.02,0.05,0.10,0.20,0.40,0.80]`, TTC `[100,200,400,800,1600,3200,6400]`
ms and 100 ms lead margin. Reuse the current-main A09 candidate/auditor bytes
by fresh SHA-256 reference; do not claim they match A09's inconsistent
historical freeze hashes. Run candidate exactly once and, only after exit 0,
the independent raw-only auditor exactly once. Retries 0. No network, pinned
Python image, read-only code/input mounts, separate outputs; request one CPU.

**D.** First require exact independent reconstruction of all 36 rows and
rejection of frozen timestamp- and track-substitution mutations. `H_PASS_SCOPED`
only if TTC strictly exceeds both simple-cue frontiers at at least one matched
false-YIELD budget. Otherwise `NO_INCREMENTAL_VALUE` (or
`NO_TTC_ADVANTAGE_UNDER_JITTER` where applicable). Protocol/integrity defects
are STOP/FAIL, not scientific promotion.

**C.** Rasterization and deterministic 2-D geometry may dominate jitter;
simple cues may suffice; stationary jitter may trigger false positives.

**U.** No real optics, tracking, DOOM, GUI, task effect, model latency,
physical release, recovery, survival, or safety claim. Pixel jitter is not a
calibrated sensor-noise model.

## Exact-main execution gate

Frozen base: `f44c5f5724ed2ba1d44cab9a8b3f88f5179c014c`. Before candidate
invocation require `origin/main` and branch merge-base to equal this SHA. If
main advances, record STOP and invoke neither formal role. The previous
successors' STOPs remain unchanged.
