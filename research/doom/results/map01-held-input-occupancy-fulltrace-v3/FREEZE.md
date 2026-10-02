# Full-trace held-input occupancy reconstruction v3 — freeze

Allocation: `MAP01-HELD-OCCUPANCY-FULLTRACE-V3-20261002-01`
Base commit: `c81e3d8ffebc7cbc2af971dfb7fb2d9b1ba1f7fe`
Type: deterministic posthoc analysis of immutable events; no model, GUI, game,
or OS input.

## H / T / D / C / U

**H.** Every started hold in the complete retained v38/v39 streams can be
represented by a conservative any-key occupancy interval, including a hold
cancelled while requested keys are only partially admitted. If no key admission
occurred, occupancy is exactly zero. If one or more ordered-prefix admissions
occurred before a verified cancel release but the runtime never emitted
`keys_held`, use lower bound zero and upper bound from first admission to
verified empty release; do not treat requested-but-unadmitted keys as active.
Normal key-up duration remains unidentified.

**T.** Run this candidate exactly once on the frozen v38 and v39 logs, then run
the independent raw-only auditor once on both outputs if both candidate runs
exit 0. Retain all outputs and hashes. Construction gates: v1 regressions 7/7,
v3 adversarial tests 5/5, source AST/byte compilation, and diff check. No
formal retry, model/GUI call, or raw-log mutation.

**D.** `PASS_FULL_TRACE_INTERVALS_SCOPED` only if every started hold has exactly
one row; full holds reconstruct by the original v1 semantics; unadmitted
cancellation yields `[0,0]`; the observed Down-only partial acquisition has
`[0, verified_release - first_admission]`; unsupported ordering, in-acquisition
observation and non-cancel release fail closed; the independent auditor reports
zero errors and reproduces all decision-window intersections.

**C.** Admission is not itself proof of a positive-duration hold. The lack of a
`keys_held` receipt means no in-hold capture certifies continued occupancy.
The lower bound therefore remains zero for partial acquisition even though one
key was acknowledged. `step_completed`, programmed duration and terminal time
are not key-up timestamps.

**U.** Two retained stochastic episodes only, with structural censoring from
missing normal key-up timestamps. No population, causal gameplay, useful-effect,
task-success, safety-rate, token, latency, or human-tempo claim.

## Predecessor disposition

The v1 full-trace candidate passed v38 (11 holds) and failed v39 because it
required `keys_held` for `cover-4:10`. The v2 successor passed v38 (11 holds)
but stopped v39 at `cover-4:10` after finding one acknowledged `Down` key and
no `space` admission before verified cancellation. Candidate counts for v2:
2; independent auditors: 0; retries: 0. Exact records remain at
`../map01-held-input-occupancy-fulltrace-v2/RUN_V2_STOP.md`; v1 and v2 freezes,
outputs, and raw events are unchanged.

## Environment / isolation boundary

At intake, read-only Docker inventory showed only `unjuno-native-ci-6092` in
`Up` state (9 hours); no exclusive container CPU slot was assigned. That
container was not inspected, stopped, or used, and no container was started.
The offline parser/auditor use local macOS arm64 / Python 3.14.5 CPU. This
successor does not claim container isolation or the separate analyzer
microbenchmark.

## Frozen source hashes

| File | SHA-256 |
|---|---|
| candidate `research/doom/analyze_map01_held_input_occupancy_fulltrace_v3.py` | `3e95222ac367cd0db85f8a5fd98ba0582623f252da0d5f98067377da3731b6e9` |
| independent auditor `research/doom/audit_map01_held_input_occupancy_fulltrace_v3.py` | `f9b55e9be1f644faf2679a8a5e15db041dadf96a330da4200b31adf16d3b0d3d` |
| construction tests `research/doom/test_map01_held_input_occupancy_fulltrace_v3.py` | `ea2bfc715a159161b70d2ff508f06abc1f12c4ab49897571eba1087ab2fdb9fd` |
| imported v1 reconstruction dependency | `ea1f71939cd2dd963cde00e8b3d8f5c726de37f75e92096e7057d805387f3ebf` |

## Frozen input hashes

| Input | SHA-256 |
|---|---|
| v38 report | `7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58` |
| v38 events | `80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3` |
| v39 report | `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687` |
| v39 events | `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381` |

Outputs are `v38.json` and `v39.json` under this directory. Candidate is run
once per input; the auditor is run once only if both candidate outputs exist.
