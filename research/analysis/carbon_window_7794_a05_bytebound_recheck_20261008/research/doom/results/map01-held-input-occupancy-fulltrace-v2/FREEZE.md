# Full-trace held-input occupancy reconstruction v2 — freeze

Allocation: `MAP01-HELD-OCCUPANCY-FULLTRACE-V2-20261002-01`
Source base: `c81e3d8ffebc7cbc2af971dfb7fb2d9b1ba1f7fe`
Type: deterministic posthoc reconstruction; zero model/GUI/game/input calls.

## H / T / D / C / U

**H.** The retained v38/v39 event streams support a conservative occupancy
interval for every started hold step. A cancellation proved to occur before any
`input_admission` has exactly zero physical input occupancy. Missing ordinary
key-up timestamps still prevent exact duration recovery.

**T.** Run the new versioned candidate once on each complete, immutable v38 and
v39 report/event stream. Separately run the raw-only auditor once on both
outputs. The auditor must bind source hashes, account for every started hold,
reconstruct every bound independently, reject unsupported partial/unacknowledged
admission, and recompute model-wait intersections. No tuning or same-version
retry. Test the candidate first on normal completion, cancellation, async
release, cancellation after focus release, pre-admission cancellation,
partial admission, wait intersection and the retained v39 cancellation sample.

**D.** `PASS_FULL_TRACE_INTERVALS_SCOPED` only if both complete outputs contain
one row for every `step_started` hold, the independent auditor reports zero
errors, the zero-admission cancellation is exactly `[0,0]`, and all intervals
are ordered/nonnegative. Exact physical duration remains `UNKNOWN` under the
retained schema; no runtime or control conclusion follows.

**C.** Normal `step_completed`, programmed duration, or final terminal time can
be later than physical key-up. An unrelated focus/expiry release can precede a
cancelled terminal. Treating partial/unacknowledged input as zero without a
verified cancel boundary can understate occupancy.

**U.** Two retained stochastic MAP01 episodes only; no population or causal
estimate. Exact normal key-up time is structurally unobserved. This is a posthoc
measurement audit, not a live allocation, game outcome, useful-feedback test,
or human-tempo comparison.

## Predecessor failure retained

The frozen v1 candidate (`research/doom/analyze_map01_held_input_occupancy_v1.py`,
SHA-256 `ea1f71939cd2dd963cde00e8b3d8f5c726de37f75e92096e7057d805387f3ebf`)
ran once on v38 and emitted `v38.json` (11 hold steps). Its single v39
invocation stopped at `AssertionError: started hold never reached keys_held:
('cover-4', 10)`. Inspection established this was an actual started step that
was cancelled before any `input_admission`; v39 terminal says
`steps_completed=10`, interruption release is verified empty with reason
`cancelled`. It is a candidate-schema limitation, not a raw-data integrity
failure. The v1 result/output and source are not modified or retried.

## Environment / resource boundary

The repo-backed container is preferred for this repeatable parser check, but
the only visible Docker container was `unjuno-native-ci-6092` (`Up 9 hours`),
and no exclusive CPU-container slot was assigned. It was not inspected, stopped
or used; no new container was started. The successor uses the complete local
repository on macOS arm64 / Python 3.14.5 for deterministic CPU-only parsing.
This does not claim the planned container benchmark or isolated environment.

## Frozen analysis code and preformal correction

One preformal candidate-test invocation first failed with a `KeyError: 'step'`
because terminal events do not carry a step field. This was a construction
failure before the full-trace candidate invocation. The check was corrected to
use the active `(program_id, step_index)` key; the unchanged v1 7/7 suite and
v2 4/4 suite then passed. This failure is preserved here, not counted as a
formal-run failure.

| File | SHA-256 |
|---|---|
| `research/doom/analyze_map01_held_input_occupancy_fulltrace_v2.py` | `53234817cd8f1ea8c09282762e2fe7b0bc872b63bf99b03dbec39107efb6051f` |
| `research/doom/audit_map01_held_input_occupancy_fulltrace_v2.py` | `6697eef2e096d8388022304365f3f4b2fe6de13f77e8bdc973802d53f98fc2ae` |
| `research/doom/test_map01_held_input_occupancy_fulltrace_v2.py` | `69b211f7a6c7a31960071a93b81fa21f9416cdc6b606e44677cbdf138a7dc540` |
| imported v1 dependency | `ea1f71939cd2dd963cde00e8b3d8f5c726de37f75e92096e7057d805387f3ebf` |

## Frozen inputs

| Input | SHA-256 |
|---|---|
| v38 report | `7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58` |
| v38 events | `80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3` |
| v39 report | `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687` |
| v39 events | `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381` |

Outputs are `v38-v2.json` and `v39-v2.json` in this additive directory;
`v38.json` remains the predecessor v1 candidate output. Historical raw
reports, events, v1 candidate and v1 failure remain unchanged.
