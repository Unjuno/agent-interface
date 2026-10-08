# Result — Issue #5734 T0

Disposition: **`METHOD_PASS_SCOPED`**. The T0 finite method gate passed; Issue
#5734's empirical hypothesis remains **unverified / HOLD**.

## Frozen question and assumptions

Before execution, `fixtures.json` fixed five sequential functions (`capture`,
`deliver`, `decide`, `guard`, `actuate`), each with a synthetic inclusive
duration range `[1,2]` integer ticks on one synthetic monotonic clock. Cue time
is 0. The loose control deadline is 11; the composed near-boundary deadline is
8. The exact Cartesian space has 32 schedules. No ranges are claimed to be
source-supported or measured. The third case has no deadline/effect oracle and
must hold. See `README.md` for H/T/D/C/U and the full boundary.

## Commands and raw outcomes

Executed from repository root using the host's Python 3 and standard library;
no network call, model, GUI, X11, game, candidate controller, or persistent
container was started by the experiment.

```text
$ python3 research/analysis/functional_coupling_5734_t0_v1/analyze.py
{"cases":[{"all_misses_local_ok":true,"case":"uncoupled_control","deadline_misses":0,"deadline_tick":11,"enumerated":32,"max_completion_tick":"10","status":"ENUMERATED","witness":null},{"all_misses_local_ok":true,"case":"coupled_near_boundary","deadline_misses":6,"deadline_tick":8,"enumerated":32,"max_completion_tick":"10","status":"ENUMERATED","witness":{"all_local_ok":true,"completion_tick":"10","deadline_miss":true,"events":[{"duration":2,"end":"2","function":"capture","local_ok":true,"start":"0"},{"duration":2,"end":"4","function":"deliver","local_ok":true,"start":"2"},{"duration":2,"end":"6","function":"decide","local_ok":true,"start":"4"},{"duration":2,"end":"8","function":"guard","local_ok":true,"start":"6"},{"duration":2,"end":"10","function":"actuate","local_ok":true,"start":"8"}] }},{"case":"missing_effect_oracle","deadline_tick":null,"enumerated":0,"status":"HOLD_NO_ORACLE"}],"schema":"functional-coupling-t0-result-v1"}
$ python3 research/analysis/functional_coupling_5734_t0_v1/audit_independent.py
{"audit":"PASS","clock_order":"single synthetic monotonic tick domain","independent_counts":{"coupled_near_boundary":[32,6],"missing_effect_oracle":"HOLD_NO_ORACLE","uncoupled_control":[32,0]},"scope":"finite synthetic T0 only"}
$ python3 -m py_compile research/analysis/functional_coupling_5734_t0_v1/analyze.py research/analysis/functional_coupling_5734_t0_v1/audit_independent.py
$ git diff --check
```

Both independent enumerators agree: the loose control has 0/32 misses; the
coupled synthetic deadline has 6/32 misses, including an exact all-max witness
at tick 10 against deadline 8, with every local interval satisfied; absent
endpoint evidence returns `HOLD_NO_ORACLE`. This is not a 6/32 risk estimate:
the enumerated schedules are not samples from any calibrated distribution.

## Verification and provenance

`analyze.py` computes event intervals as exact `Fraction` values and emits a
canonical schedule witness. `audit_independent.py` does not import the candidate
analyzer; it separately enumerates the Cartesian product, checks every local
bound, recomputes endpoint sums, verifies expected counts, and checks the HOLD
case. Both commands exited 0; syntax compilation and `git diff --check` passed.
The fixture was committed before these commands ran. `SHA256SUMS` records the
retained source and frozen input hashes.

Branch `research/functional-coupling-5734-t0-20261001` starts at the then-current
main SHA `3ed5d7865daaaf202c59054c3545ade968446fc8` (verified with `git ls-remote`
before branch creation). The Docker/OrbStack environment was deliberately not
started: the ongoing #5156 X11 allocation has unresolved ownership for existing
Created containers and a reported unresponsive Docker Desktop. T0 itself is a
pure finite CPU calculation, so it ran host-local without touching that shared
resource. This is a method-level experiment, not a container/runtime allocation.

## Decision and limits

- T0 gate: **PASS**, `METHOD_PASS_SCOPED`.
- Full H: **HOLD / unverified**. There is no source-supported timing envelope,
  empirical effective-action or harm oracle, held-out schedule, or equal-budget
  comparison to #5327/#5330 baselines.
- No Agent Interface hazard, preventable harm, safety proof, causal claim,
  calibrated probability, or actual runtime effect is established.
- Next eligible empirical work requires independently timestamped cue,
  effective-action and harm/deadline endpoints plus measured local ranges. Only
  then freeze a held-out matched comparison. If those endpoints remain absent,
  stop at HOLD rather than impute a deadline.
