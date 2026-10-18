# Issue #8112 — A06 boundary-jitter robustness experiment

Fresh successor to A01/A02/A03/A05 exact-main STOPs and A04 auditor input-schema
failure. All predecessor outcomes remain unchanged; no consumed allocation is
replayed.

## H / T / D / C / U

**H.** On a finite synthetic approach fixture with irregular timestamps,
independently randomized ±1–3 px apparent-radius boundary jitter can reduce or
eliminate secant-TTC's ability to detect contact at least 100 ms early compared
with pixel-change and relative-area-growth thresholds at the same false-YIELD
budget. No advantage is assumed.

**T.** Fresh seed 20261014; 36 opaque-ID 256×256 PGM sequences, five frames
each, contact radius 96 px, timestamps `[0,220,610,1180,1800]` ms. 24
constant-speed approaches (six each at jitter amplitudes 0–3 px, independent
bounded per-frame radius offsets) and 12 controls covering stationary jitter,
camera/background scale, lateral translation, occlusion, track swap and
timestamp regression. Candidate sees only IDs, timestamps, tracks and frame
paths; family/jitter/contact truth remains auditor-only. Use #5905 A06 frozen
pixel/area/TTC thresholds and 100 ms lead margin. Reuse current-main A09
candidate/auditor bytes by fresh SHA reference; historical A09 hash mismatch is
disclosed, not papered over. The truth sidecar root is a list of case records,
matching the retained auditor's input contract (A04's rejected object wrapper
is not reused). Run candidate once then separate raw-only auditor once; retries
0. Network disabled, digest-pinned Python image, read-only code/input, separate
outputs, one CPU requested.

**D.** Require auditor reconstruction of all 36 rows and rejection of frozen
timestamp/track substitution controls. `H_PASS_SCOPED` only if TTC strictly
beats both simple-cue frontiers at at least one matched false-YIELD budget;
otherwise `NO_INCREMENTAL_VALUE` / `NO_TTC_ADVANTAGE_UNDER_JITTER`. Integrity
errors are STOP/FAIL, not scientific results.

**C.** Rasterization and 2-D geometry may dominate jitter; simple cues may
suffice; stationary jitter can induce false positives.

**U.** No real optics/tracking, game, GUI, task effect, model latency, physical
release, recovery, survival, or safety claim. Pixel jitter is not calibrated
sensor noise.

Freeze current `origin/main` only when branch merge-base matches it. Immediately
before candidate invocation, fetch main again and require exact equality with
the frozen SHA or preserve a pre-candidate STOP.
