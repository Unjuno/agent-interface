# Prospective one-shot protocol — Issue #6358

Allocation: `ADOPTION-CONDITIONED-RECOURSE-6358-T0-MAC-HOST-20261003-01`
Frozen main after preformal refresh: `fc1c09294458d3b2744fa05432d4cf8a19583f18`
Prior allocation: `ADOPTION-CONDITIONED-RECOURSE-6358-T0-HOST-20261002-01` (preserved `STOP_RUNNER_REDIRECTION_DIRECTORY_MISSING`; candidate program invocations 0; no retry)

## H / T / D / C / U

- **H:** In the frozen synthetic shared-capacity fixture, individually feasible advice can become collectively infeasible under synchronized adoption; predeclared recipient-specific authorized routing can preserve verified cohort outcomes without suppressing valid work or weakening safety. This should not help under disjoint resources or ample capacity.
- **T:** One local CPU-only candidate invocation over the immutable eight-case/seven-policy fixture, followed—only on candidate exit 0—by one independent raw-only auditor invocation. The previous allocation's candidate never started; this is a new ID, new output path, new host runtime and prospectively frozen run, not a continuation or relabelling.
- **D:** `PASS_METHOD_SCOPED` only if candidate, independent audit, corruption controls and frozen primary/control comparisons all pass. Otherwise retain exact FAIL/HOLD/STOP. Synthetic output is not causal or deployment evidence.
- **C:** Cases and method unchanged from the referenced preregistered v2; candidate/auditor allocation IDs changed. One candidate, one conditional auditor, no retries, tuning, network, model, GUI, GPU, container, production service or actual retry/actuation.
- **U:** One Mac host, CPython 3.14.5, deterministic synthetic scheduler. No claim about real multi-agent/human adoption, prevalence, production capacity, or end-to-end task benefit.

## Preflight and invocation

1. Confirm GitHub `main` is still the frozen SHA and source hashes match `FREEZE.json`.
2. Run only construction unit tests and `git diff --check` before the formal allocation.
3. Confirm `results/formal-01/` does not exist. Freeze files before candidate invocation.
4. Run the candidate once; record argv/stdout/stderr/exit. Run the independent auditor once only if candidate exits zero. Any issue after candidate start is retained without retry.

```sh
python3 -B candidate.py --cases cases.json --out results/formal-01/candidate.raw.json
python3 -B auditor.py --cases cases.json --candidate results/formal-01/candidate.raw.json --out results/formal-01/audit.raw.json
```

The second command is conditional on candidate exit 0. Formal output directory is fresh. If the experiment cannot run, preserve STOP; do not launch a substitute container or repeat under this allocation.
