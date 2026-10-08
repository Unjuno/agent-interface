# Model-free typed cover-validity replay

`map01-cover-validity-replay-v1` is a development construction replay over two
retained real Freedoom MAP01 allocations. It tests whether exact HUD health can
replace directionless changed-pixel invalidation and whether an already admitted
bounded policy can distinguish soft observable change from a hard contract
breach. It makes zero model calls and grants zero new input authority.

## Deterministic signal boundary

`doom_hud_signal_v1.py` reads `PLAYPAL` and `STTNUM0` through `STTNUM9` directly
from the hash-checked Freedoom WAD. It renders those Doom patch glyphs, scales
them to the observed 640x480 HUD, and matches their foreground RGB values in a
window-relative three-slot region. The reader requires the expected WAD hash,
exact observation metadata and the frozen client geometry. Missing images,
unsupported geometry, invalid bindings and ambiguous digits return `unknown`.

The generic `ObservableSignalGuard` accepts a source value and a typed hard
minimum. An unchanged or soft value may only preserve authority that was already
admitted. A value below the minimum, expiry, unknown signal, binding mismatch or
nonadvancing evidence requires a new decision. No outcome can authorize input.
The monitor coalesces repeated soft samples while retaining the newest distinct
soft event for the planner.

## Retained evidence

The reader extracts health from all 70 exact v28 observations with zero unknown
results. Nineteen manually reviewed values across two allocations match:

- v28 review points include `100, 97, 100, 93, 87, 81, 79, 73`; the increase
  from 97 to 100 exposes a pickup that a directionless pixel-change guard cannot
  classify;
- an independent v23 trace contributes 12 hash-checked retained decision frames
  with reviewed values `100, 100, 100, 100, 97, 74, 28, 28, 28, 28, 28, 28`.

The development-only candidate uses v28 sequence 37 at health 93 and a posthoc
hard minimum of 80. It coalesces health 87 and 81 as two soft transitions, then
reports a hard invalidation at health 79. Relative to v28's first raw HUD change,
the hard event occurs 17 exact samples and 5,240.235886 ms later. On this machine
and replay, extraction median/p95/max are recorded in the retained report rather
than treated as general rates.

## Interpretation and limits

This passes the deterministic extraction, one-way authority, fail-closed and
event-coalescing construction checks. It shows that an earlier rejected
single-ROI idea becomes useful under a narrower condition: it is a source for a
typed observable value, not evidence of success and not permission to act.

The floor of 80 was selected after inspecting this trace. The replay does not
show that a planner would finish before the hard event, that preserving cover
improves survival or progress, or that an integrated hard event releases input
within the existing live safety envelope. It establishes no token, gameplay,
latency, reliability, human-speed or MAP01-clear advantage.

The next integration must make the validity envelope part of the admitted typed
cover, bind it to the exact source signal, and exercise soft preservation plus
hard cancellation without changing the existing release and stale-plan rules.
A separately frozen live allocation is justified only after that model-free
controller path passes.

## Reproduce

```powershell
python -m unittest research.doom.test_doom_hud_signal_v1 research.live_control.test_observable_signal_guard_v1 -q
python research/doom/probe_map01_cover_validity_replay_v1.py --out results-local/doom/map01-cover-validity-replay-v1-new
python research/doom/audit_map01_cover_validity_replay_v1.py
```

The retained report and audit are in
`research/doom/results/map01-cover-validity-replay-v1/`.
