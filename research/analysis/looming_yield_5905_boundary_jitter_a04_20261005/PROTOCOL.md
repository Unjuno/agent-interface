# Issue #8112 — A04 boundary-jitter robustness experiment

Fresh successor to A01/A02/A03, each stopped before formal execution because
main advanced. None of those allocations is relaunched; their frozen evidence
remains intact.

## H / T / D / C / U

**H.** On a finite synthetic approach fixture with irregular timestamps,
independently randomized ±1–3 px apparent-radius boundary jitter can reduce or
eliminate secant-TTC's ability to detect contact at least 100 ms early compared
with pixel-change and relative-area-growth thresholds at the same false-YIELD
budget. No advantage is assumed.

**T.** Fresh seed 20261012; 36 opaque-ID 256×256 PGM sequences, five frames
each, contact radius 96 px, timestamps `[0,220,610,1180,1800]` ms. 24
constant-speed approaches (six each at jitter amplitudes 0–3 px; independent
bounded per-frame radius offsets) and 12 controls: stationary size jitter,
camera/background scale, lateral translation, occlusion, track swap, timestamp
regression. Candidate sees only opaque IDs, timestamps, track IDs, and frame
paths; family/jitter/contact truth are auditor-only. Compare #5905 A06 frozen
pixel/area/TTC thresholds and 100 ms lead margin from this H/T specification.
Reuse current-main A09 candidate/auditor bytes by fresh SHA reference; A09
historical hash mismatch is disclosed and not represented as continuity. One
candidate call then one separate raw-only auditor call, zero retries, no
network, pinned image, read-only code/input, distinct outputs, one CPU requested.

**D.** Independently reconstruct 36/36 rows and reject timestamp/track
substitution mutations. `H_PASS_SCOPED` only when TTC exceeds both simple-cue
frontiers at one or more matched false-YIELD budgets. Otherwise report
`NO_INCREMENTAL_VALUE` / `NO_TTC_ADVANTAGE_UNDER_JITTER`. Any integrity or
protocol defect is STOP/FAIL, not a scientific result.

**C.** Rasterization and deterministic geometry may dominate jitter; simple
cues may suffice; stationary jitter may produce false positives.

**U.** No real optics/tracking, game, GUI, task effect, model latency, physical
release, recovery, survival, or safety claim. Synthetic pixel jitter is not a
calibrated sensor-noise model.

## Allocation gate

The base SHA is selected and frozen by `prepare_freeze.py` from the current
`origin/main` only after the branch is rebased. `execute_formal.py` fetches
main, freezes inputs, then `run_formal.py` fetches main again immediately
before the candidate gate; both `origin/main` and merge-base must equal the
frozen SHA. Any advance is retained as a pre-candidate STOP.
