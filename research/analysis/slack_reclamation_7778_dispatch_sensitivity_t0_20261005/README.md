# Issue #7778 T0 — bounded slack reclamation

This package tests a finite scheduler model only. It does not change host
scheduling, Docker/OrbStack settings, GUI input, runtime behavior, or establish
physical release timing.

## Frozen question

On a one-CPU, integer-slot model, can a demand-guarded slack-stealing policy
preserve every control deadline that is feasible under the declared finite
sporadic-release envelope while completing more best-effort work than a static
`Q=2, P=8` reservation? Does the policy refuse to make a deadline-safety claim
for infeasible or out-of-model inputs?

The three policies are `PRIORITY_ONLY`, `STATIC_RESERVATION`, and
`DEMAND_GUARDED_SLACK_STEAL`. Unused static control budget expires; it is not
made available to best-effort work. All policies receive the same one-CPU,
one-unit-per-slot capacity. Each case has one to three control jobs, two
different-sized best-effort jobs, and fixed candidate release choices. The
guard sees the declared finite release envelope and already observed arrivals,
not the selected future release times.

`cases.json` is generated from fixed seeds 777800–777815 plus two frozen
boundary controls (seed IDs 777898 and 777899). The two late-release profiles
(8 cases total) are the preregistered positive-slack subset: control arrivals
cannot occur before tick 16 while best-effort jobs are ready at tick 0. The matrix includes
same-boundary bursts, exact demand equality, jointly infeasible demand, and
same-stream minimum-interarrival constraints. Per-job dispatch overhead of 0
or 1 CPU slot is a frozen sensitivity factor; it is charged once before that
job's first payload unit.

## Gates

- `PASS_METHOD_SCOPED`: raw events reconstruct exactly; every fixed job and
  release is accounted for; capacity and static server caps hold; the
  independent exhaustive slot scheduler agrees on feasibility and maximum
  best-effort payload; every granted slack slot survives every remaining
  allowed release schedule; unknown job classes, WCET, and non-preemptive work
  fail closed; all retained mutation controls are rejected.
- `H_PASS_SCOPED`: in every exhaustive-oracle-feasible case, guarded slack
  misses no control deadline; on the frozen positive-slack subset, it executes
  strictly more best-effort payload units than static reservation at the same
  CPU capacity. Infeasible cases remain labeled infeasible and are not counted
  as safety successes.
- Otherwise report `FAIL`/`HOLD` with the exact gate; no tuning, retry, or
  promotion to host, OS, container, GUI, physical-release, latency, or product
  claims.

## H / T / D / C / U

- **H:** on each feasible workload in this finite model, the demand guard meets
  every control deadline and completes strictly more best-effort payload than
  static reservation over the frozen positive-slack subset. A feasible-case
  miss or no positive-slack gain falsifies the scoped hypothesis.
- **T:** execute 18 frozen traces with 1–3 control obligations, bursty release
  windows, varied hard-work/deadline values, and two different-sized soft jobs.
  Compare all three policies at dispatch-overhead factors 0 and 1. An independent
  auditor exhaustively enumerates unit-slot schedules for control feasibility
  and maximum soft payload, and rejects class, capacity, release, reservation,
  and deadline mutations.
- **D:** method PASS requires exact input/event reconstruction, agreement with
  exhaustive feasibility/soft-work bounds, safe slack grants for every
  remaining release assignment, and fail-closed refusal controls. H PASS
  requires zero guarded misses on all oracle-feasible traces at both overhead
  factors and more soft payload than static on the frozen subset at overhead 0.
  Infeasible cases are reported and never counted as safe.
- **C:** priority-only may already preserve deadlines and reclaim idle slots;
  static reservation may provide enough control service without meaningful
  waste; dispatch cost may erase the reclaimed service. CPU dispatch may also
  be irrelevant to physical input-release delay.
- **U:** the result applies only to the discrete single-CPU simulator and its
  finite release envelope. It does not establish actual execution bounds,
  OS/cgroup/container enforcement, GUI effects, key-up, physical release,
  runtime safety, or end-to-end latency.

## Execution record

OrbStack's daemon endpoint answered version/info requests, but image listing and
inspection failed with a containerd content-blob `operation not supported`
error. Repeated Docker access was stopped. Since this finite arithmetic model
uses no container feature and makes no timing/resource-isolation claim, the
candidate and independent audit use host CPython as a separately labeled
fallback (CPython 3.14.5 on the local ARM64 host). This does not count as a
container-backed run or as Python 3.12 CI evidence. The construction test output
is retained in `CONSTRUCTION_TESTS.log`.

Construction test:

```sh
python -B build_cases.py
python -B -m unittest -v test_method.py
```

Formal candidate and auditor are each run once after the exact code, case
matrix, and freeze hashes are recorded in `FREEZE.json`:

```sh
python -B candidate.py --cases cases.json --out result/raw.jsonl --refusals result/refusals.json
python -B auditor.py --raw result/raw.jsonl --refusals result/refusals.json --cases cases.json --out result/audit.json
```

The candidate run is not repeated to repair an outcome. Construction tests and
post-run archive-integrity checks are distinct from those two formal runs.
