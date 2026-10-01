# Result — Issue #5734 T0-v2

Disposition: **`METHOD_PASS_SCOPED` for finite synthetic DAG mechanics only**.
Full empirical H remains unverified / HOLD. T0-v2 is a separately frozen
successor after the v1 control-topology defect was discovered; v1 remains intact
and its narrowed disposition is recorded in `../functional_coupling_5734_t0_v1/DESIGN_REVIEW.md`.

## Preregistered setup

Before execution, the issue comment recorded two explicit graphs over five
functions, each with synthetic duration `[1,2]` ticks: (1) all functions
independent from cue time 0, deadline 2; (2) a five-stage sequential dependency
chain, deadline 8; and (3) a chain with no endpoint oracle. There are 32 exact
duration assignments per measured graph. These are analyst-authored mechanics,
not source-supported timing ranges, samples, or calibrated distributions.

## Commands and raw results

Executed from repository root with host Python 3 standard library. No model,
GUI, X11, game, persistent container, or runtime candidate was started.

```text
$ python3 research/analysis/functional_coupling_5734_t0_v2/analyze.py
{"cases":[{"all_misses_local_ok":true,"case":"parallel_control","deadline_misses":0,"deadline_tick":2,"enumerated":32,"max_completion_tick":"2","status":"ENUMERATED","witness":null},{"all_misses_local_ok":true,"case":"coupled_chain","deadline_misses":6,"deadline_tick":8,"enumerated":32,"max_completion_tick":"10","status":"ENUMERATED","witness":{"all_local_ok":true,"completion_tick":"10","deadline_miss":true,"events":[{"duration":2,"end":"2","function":"capture","local_ok":true,"start":"0"},{"duration":2,"end":"4","function":"deliver","local_ok":true,"start":"2"},{"duration":2,"end":"6","function":"decide","local_ok":true,"start":"4"},{"duration":2,"end":"8","function":"guard","local_ok":true,"start":"6"},{"duration":2,"end":"10","function":"actuate","local_ok":true,"start":"8"}] }},{"case":"missing_effect_oracle","deadline_tick":null,"enumerated":0,"status":"HOLD_NO_ORACLE"}],"schema":"functional-coupling-t0-v2-result-v1"}
$ python3 research/analysis/functional_coupling_5734_t0_v2/audit_independent.py
{"audit":"PASS","independent_graph_counts":{"coupled_chain":{"deadline_misses":6,"max_completion_tick":"10","schedules":32},"missing_effect_oracle":"HOLD_NO_ORACLE","parallel_control":{"deadline_misses":0,"max_completion_tick":"2","schedules":32}},"scope":"synthetic finite T0-v2 only"}
$ python3 -m py_compile research/analysis/functional_coupling_5734_t0_v2/analyze.py research/analysis/functional_coupling_5734_t0_v2/audit_independent.py
$ git diff --check
```

Both graph enumerators agree: parallel control 0/32 deadline misses (maximum
completion 2); sequential chain 6/32 (maximum 10, deadline 8), with every local
duration legal; missing endpoint oracle returns `HOLD_NO_ORACLE`. The 6/32 is
not an estimated risk probability because no sampling distribution exists.

The primary implementation schedules predecessor events using exact
`Fraction` arithmetic. The independent auditor does not import it; it builds
predecessor lists separately, exhaustively schedules ready nodes, validates all
local domains, and checks full counts and extrema. Both commands exited 0;
syntax compilation and whitespace checks passed. `SHA256SUMS` retains hashes.

## Resource and decision boundary

Docker/OrbStack was not started because shared #5156 X11 containers still lack
resolved ownership/release evidence. The experiment is a finite synthetic CPU
calculation only. It does not test the empirical Issue hypothesis: no timing
range comes from a source-bound real system; there is no effective-action/harm
oracle, calibrated variability/correlation, held-out schedule, or fair,
equal-budget comparison to #5327/#5330. It establishes no real hazard, harm,
safety, causal effect, or product capability. T1 remains HOLD until independent
cue/effective-action/harm endpoints and measured local ranges exist.
