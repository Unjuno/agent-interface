# Issue #5413 — causal reobserve boundary T0

Frozen source main: `2197bead5ffa7dc226390becc811913159c8438e`.

## H / T / D / C / U

- **H:** A reobserve request is not itself fresh evidence. Invalidation may be cleared only by an observation linked to the currently pending request, bound to the current generation, and strictly newer than the sequence at invalidation. Repeated polling must not emit duplicate requests; any action while invalid remains blocked.
- **T:** Exhaustively run every trace of length 0–4 over seven deterministic events: `INVALIDATE`, `POLL`, `OBS_MATCH`, `OBS_UNLINKED`, `OBS_REPLAY`, `OBS_OLD_REQUEST`, and `ACT`. Retain candidate transcripts for every trace. Run one fixed unit suite, one enumerator, and one separate raw-only auditor with five frozen corruptions.
- **D:** Pass this boundary construction only if the independent reference reconstructs all 2,801 traces exactly, accepts actions only after a causally linked fresh observation in the current generation, never lets an unlinked/replayed/superseded response clear invalidation, emits at most one request per invalidation generation despite repeated polls, and rejects all five corruptions. Any false admission or audit mismatch is STOP/FAIL; no retries.
- **C:** Finite synthetic host-CPU event machine. Inputs model request IDs, generations, and observation sequence numbers as trusted labels; they are not connected to a real capture channel, monotonic clock, X11, MAP01, or task effect.
- **U:** This checks only a causal-link invariant in a bounded abstract trace. It does not show live reobserve usefulness, latency benefit, safety under hidden GUI changes, or resolve Issue #59. No Docker/GPU/model work is needed for this finite machine.

## Fixed semantics

State begins at generation 0 with observation sequence 0 and a valid observation. `INVALIDATE` increments generation, marks stale, and supersedes any older pending request with a new generation-bound ID. `POLL` emits exactly one pending request if stale and none exists. `OBS_MATCH` is the only event that supplies the pending request ID, current generation, and a sequence strictly greater than the invalidation baseline. `OBS_UNLINKED`, `OBS_REPLAY`, and `OBS_OLD_REQUEST` deliberately violate one of those bindings. `ACT` is admitted only when the current generation has a valid observation and no invalidation remains.

The independent auditor uses a separately written reference transition function and never imports candidate code.
