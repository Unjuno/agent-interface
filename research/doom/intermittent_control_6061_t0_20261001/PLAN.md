# Issue #6061 T0 — prediction-error-triggered motor chunks

## Status and qualification

One-shot deterministic finite-fixture method experiment. This is not a live game, GUI, model, physical-input, human-tempo, or runtime result. The frozen T0 requested an isolated container fixture. Docker Desktop's Windows service was observed stopped and the `docker version` server query remained live without a server response, then was interrupted; because shared-container ownership is unresolved in #5085, no service start, inventory mutation, or container launch was attempted. Execution therefore uses host CPython as a disclosed environment deviation. The mathematical fixture remains the same; container isolation is not claimed.

## H / T / D / C / U

- **H:** For the declared finite target trajectories, prediction-error-triggered chunks preserve exact task effect and invalidation safety at least as well as fixed-period control while reducing expensive full captures relative to fixed-period control; the nonpredictive bounded-hold arm reveals whether prediction adds value beyond chunking.
- **T:** One candidate simulation over nine frozen dynamic cases and four policies (fixed-period, prediction-triggered, bounded sample-and-hold, one-tick/no-continuation). All policies share the same initial state, 40-tick horizon, input authority, 8-tick maximum chunk, and total 40-tick occupancy ceiling. Full-capture cadence is 4 ticks for fixed control; event-trigger threshold is 2 coordinate units with an 8-tick maximum chunk. A separate inexpensive tracker probe is provided at each tick; the predictive policy may use only this declared probe, never auditor truth. Cases cover steady drift, abrupt reversal, disappearance, misleading animation, same-kinematics semantic identity switch, focus loss, lease expiry, a perfect-tracker control, and a stale-tracker negative control.
- **D:** `PASS_METHOD_SCOPED` only if the independent auditor reconstructs every action/position/occupancy/capture/trigger from the frozen observable fixture, verifies the truth-side effect oracle separately, sees zero action after identity/focus/lease/target invalidation, and confirms the perfect/stale tracker controls behave as preregistered. The directional efficiency hypothesis is supported only if predictive control retains the fixed arm's task-effect successes and safety while strictly reducing full captures; otherwise report the observed counterexample/frontier without widening scope.
- **C:** Synthetic coordinates, deterministic tick clock, one-dimensional plant, perfect timestamp alignment, fixed action speed, declared identity/focus/lease channels, and idealized per-tick cheap tracker. A real GUI may not provide these signals or costs.
- **U:** No real predictor quality, physical key occupancy, release latency distribution, task utility beyond the frozen proximity oracle, safety under OS scheduling, cross-domain transfer, or #59 live-control result is established.

## Frozen interfaces and one-shot rule

`input_fixture.json` is the only input visible to the candidate. `truth_oracle.json` is auditor-only. `candidate.py` produces exactly one JSONL raw file; `audit.py` reads that raw file once and independently reconstructs all 36 case-policy trajectories. Candidate and auditor are each invoked at most once; no retry or repair after either formal invocation. The frozen source/input identities are recorded in `FREEZE.json` before the candidate invocation. Construction tests do not read candidate raw output.

## Protocol deviation

No container image, Docker context inventory, image build/pull, GUI, network, model, GPU, external input, cleanup, or shared execution lane was used. Host interpreter and full commands are recorded in `RUN.json`. This substitution narrows environment claims; it does not turn a method PASS into container or live evidence.
